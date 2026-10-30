"""Telegram front end for the agent: send the bot a photo, get the cleaned copy back with what was hidden and what a
stranger could still learn. Same agent, model settings and access code (LIVE_CODE) as the web page. Standard library
only for the network, so it adds no dependency.

Run:       uv run --env-file .env python -m app.telegram_bot      (TELEGRAM_BOT_TOKEN from @BotFather)
Self-check, no token and no network:  uv run python -m app.telegram_bot --selftest
"""
import base64
import functools
import hmac
import json
import logging
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

from . import agent, meta, pipeline

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CODE = os.environ.get("LIVE_CODE") or None  # the site's access code; /unlock <code> in the chat
PER_HOUR = int(os.environ.get("BOT_RUNS_PER_HOUR", "3"))  # photos per chat per hour: the model's quota is the limit
MAX_SIDE = 2048
MAX_BYTES = 20 * 1024 * 1024
LEVELS = {1: "broad", 2: "narrowed", 3: "specific", 4: "exact"}
WHAT = {"home_location": "Where you live", "current_location": "Where this was taken", "work_or_school": "Work or school",
        "identity": "Who you are", "contact": "How to reach you", "routine": "Your routine",
        "financial_or_id": "ID and account numbers", "other_people": "People around you"}
LANGUAGES = "en (English), te (Telugu), hi (Hindi)"
HELP = ("Send me a photo before you post it. I look at it the way a stranger would, hide only what gives you away "
        "(ID numbers, number plates, addresses, UPI IDs, labels), and check again. A check takes a minute or two.\n\n"
        "Send the photo as a file to keep its full quality.\n\n"
        "/lang en|te|hi  the language of my report (" + LANGUAGES + ")\n"
        "/unlock <code>  the access code, if the team gave you one\n"
        "/help           this message\n\n"
        "Your photo is only held in memory while it is checked, and is sent to the model's host to find the clues.")

log = logging.getLogger("telegram_bot")
jobs: queue.Queue = queue.Queue()  # (chat id, file id, language): one check at a time
working = threading.Event()
unlocked: set[int] = set()
language: dict[int, str] = {}
recent: dict[int, list[float]] = {}
_lock = threading.Lock()


# The network layer: three small functions, so the self-check can replace them. Errors never carry the URL (it holds the token).
def _post_json(method: str, params: dict, timeout: float = 70) -> dict:
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:  # Telegram explains 4xx errors in a JSON body
        return json.loads(e.read() or b"{}")


def _post_form(method: str, fields: dict, files: dict, timeout: float = 120) -> dict:
    boundary = uuid.uuid4().hex
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
    for k, (name, data, ctype) in files.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\n'
                     f"Content-Type: {ctype}\r\n\r\n".encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=b"".join(parts),
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


def _get(file_path: str, timeout: float = 60) -> bytes:
    with urllib.request.urlopen(f"https://api.telegram.org/file/bot{TOKEN}/{file_path}", timeout=timeout) as r:
        return r.read(MAX_BYTES + 1)


def api(method: str, **params):
    data = _post_json(method, params)
    if not data.get("ok"):
        raise RuntimeError(f"{method} failed: {data.get('description')}")
    return data["result"]


def say(chat_id: int, text: str) -> int:
    return api("sendMessage", chat_id=chat_id, text=text[:4096])["message_id"]


def send_document(chat_id: int, data: bytes, name: str, caption: str) -> None:
    if not _post_form("sendDocument", {"chat_id": str(chat_id), "caption": caption[:1024]},
                      {"document": (name, data, "image/png")}).get("ok"):
        raise RuntimeError("sendDocument failed")


def download(file_id: str) -> bytes:
    info = api("getFile", file_id=file_id)
    if info.get("file_size", 0) > MAX_BYTES:
        raise ValueError("file too large")
    data = _get(info["file_path"])
    if len(data) > MAX_BYTES:
        raise ValueError("file too large")
    return data


class Progress:
    """One message that is edited as the agent moves along, at most every few seconds."""

    def __init__(self, chat_id: int, text: str):
        self.chat_id, self.last, self.at = chat_id, text, time.monotonic()
        self.id = say(chat_id, text)

    def update(self, text: str) -> None:
        if text == self.last or time.monotonic() - self.at < 3:
            return
        try:
            api("editMessageText", chat_id=self.chat_id, message_id=self.id, text=text)
            self.last, self.at = text, time.monotonic()
        except Exception as e:  # a failed progress edit must never stop the check
            log.warning("progress edit failed: %s", type(e).__name__)


def report(summary: str, done: dict) -> str:
    """What the reply says: the model's summary, before and after per kind of exposure, what was hidden, and an honest verdict."""
    lines = [summary] if summary else []
    rows = [f"- {WHAT.get(c, c)}: {LEVELS.get(lvl, lvl)} -> {LEVELS.get(done['after'].get(c, 0), 'nothing')}"
            for c, lvl in sorted(done["before"].items(), key=lambda kv: -kv[1])]
    if rows:
        lines += ["", "What a stranger could learn, before -> after:", *rows]
    hidden = [h["label"] for h in done["hidden"]]
    if hidden:
        lines += ["", "Hidden: " + ", ".join(hidden)]
    if done["safe"]:
        verdict = ("My own re-check found nothing specific left. That is my judgment, not a guarantee, so look at "
                   "the picture before you post it.")
    elif done["unverified"]:
        verdict = "The re-check did not finish, so this copy is not verified. Look at it carefully before you post."
    elif done["doubt"]:
        verdict = "Text in the photo tried to talk the checker out of reporting, so this copy is not verified."
    else:
        verdict = "Something specific may still be visible. Look at the picture before you post it."
    return "\n".join(lines + ["", verdict])


def run_job(chat_id: int, file_id: str, lang: str) -> None:
    progress = Progress(chat_id, "Reading your photo...")
    try:
        img, _ = pipeline.load_image(download(file_id), MAX_SIDE)
    except Exception as e:
        log.warning("could not open a photo: %s", type(e).__name__)
        say(chat_id, "I could not open that file. Send a JPEG, PNG or WebP photo, up to 20 MB.")
        return
    private = meta.open_client is not None
    attack = functools.partial(meta.attack, private=True, lang=lang) if private else meta.mock_attacker()
    read = functools.partial(meta.read_text, private=True, effort=meta.ATTACK_EFFORT) if private else None
    summary, done = "", None
    for event in agent.run([img], attack=attack, private=True, read=read):
        if event["type"] in ("status", "plan") and event.get("text"):
            progress.update(event["text"] + "...")
        elif event["type"] == "attack" and not summary:
            summary = event["graph"].get("summary", "")
        elif event["type"] == "done":
            done = event
    png = base64.b64decode(done["images"][0])
    text = report(summary, done)
    if len(text) <= 1024:
        send_document(chat_id, png, "safe-copy.png", text)
    else:
        send_document(chat_id, png, "safe-copy.png", "Your safe copy: no EXIF or GPS data.")
        say(chat_id, text)


def worker() -> None:
    while True:
        chat_id, file_id, lang = jobs.get()
        working.set()
        try:
            run_job(chat_id, file_id, lang)
        except Exception as e:
            log.exception("check failed")
            try:
                say(chat_id, "The check hit an error before it finished (" + type(e).__name__ + "). Try again in a minute.")
            except Exception:
                pass
        finally:
            working.clear()


def allow(chat_id: int) -> bool:
    now = time.time()
    with _lock:
        runs = [t for t in recent.get(chat_id, []) if now - t < 3600]
        if len(runs) >= PER_HOUR:
            recent[chat_id] = runs
            return False
        recent[chat_id] = runs + [now]
        return True


def handle(update: dict) -> None:
    msg = update.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    if chat_id is None:
        return
    text = (msg.get("text") or "").strip()
    if text.startswith("/"):
        cmd, _, arg = text.partition(" ")
        cmd, arg = cmd.split("@")[0].lower(), arg.strip()
        if cmd in ("/start", "/help"):
            say(chat_id, HELP)
        elif cmd == "/lang":
            if arg in meta.LANGS:
                language[chat_id] = arg
                say(chat_id, f"Reports will be in {meta.LANGS[arg]}. The edits are the same.")
            else:
                say(chat_id, "Choose one of: " + LANGUAGES + ". For example /lang te")
        elif cmd == "/unlock":
            if CODE and hmac.compare_digest(arg.encode(), CODE.encode()):
                unlocked.add(chat_id)
                say(chat_id, "Unlocked. Send me a photo.")
            else:
                say(chat_id, "That code does not match.")
        else:
            say(chat_id, "I do not know that command. /help lists them.")
        return
    file_id = None
    if msg.get("photo"):
        file_id = msg["photo"][-1]["file_id"]  # the largest size Telegram kept
    elif (msg.get("document") or {}).get("mime_type", "").startswith("image/"):
        file_id = msg["document"]["file_id"]
    if not file_id:
        say(chat_id, "Send me a photo and I will check it. /help explains how.")
        return
    if CODE and chat_id not in unlocked:
        say(chat_id, "Send /unlock followed by the access code first. Ask the team for it.")
        return
    if not allow(chat_id):
        say(chat_id, f"That is the limit of {PER_HOUR} photos an hour for this chat. Try again later.")
        return
    ahead = jobs.qsize() + (1 if working.is_set() else 0)
    jobs.put((chat_id, file_id, language.get(chat_id, "en")))
    if ahead:
        say(chat_id, f"Got it. {ahead} photo{'s' if ahead != 1 else ''} ahead of yours.")


def poll() -> None:
    offset = 0
    while True:
        try:
            updates = api("getUpdates", offset=offset, timeout=50, allowed_updates=["message"])
        except Exception as e:
            log.warning("getUpdates failed: %s", type(e).__name__)
            time.sleep(5)
            continue
        for update in updates:
            offset = update["update_id"] + 1
            try:
                handle(update)
            except Exception:
                log.exception("update failed")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN: open Telegram, talk to @BotFather, send /newbot, copy the token into .env.")
    me = api("getMe")
    log.info("bot @%s is running; model: %s; access code %s", me.get("username"),
             meta.OPEN_LABEL if meta.open_client else "none (placeholder attacker)", "required" if CODE else "off")
    threading.Thread(target=worker, daemon=True).start()
    poll()


def selftest() -> None:
    """The whole flow against a fake Telegram, with the placeholder attacker: no token, no network, no model."""
    import io

    from PIL import Image

    global TOKEN, CODE, PER_HOUR, _post_json, _post_form, _get
    TOKEN, CODE, PER_HOUR = "TEST", "letmein", 3
    meta.open_client = None  # force the placeholder attacker even when a key is in the environment
    buf = io.BytesIO()
    Image.new("RGB", (640, 480), (200, 190, 170)).save(buf, "PNG")
    photo = buf.getvalue()
    calls, documents = [], []

    def fake_json(method, params, timeout=70):
        calls.append((method, params))
        result = {"file_path": "photos/a.png", "file_size": len(photo)} if method == "getFile" else {"message_id": 7}
        return {"ok": True, "result": result}

    def fake_form(method, fields, files, timeout=120):
        documents.append((method, fields, files))
        return {"ok": True, "result": {}}

    _post_json, _post_form, _get = fake_json, fake_form, lambda file_path, timeout=60: photo

    def sent():
        return [p["text"] for m, p in calls if m == "sendMessage"]

    chat = {"chat": {"id": 42}}
    handle({"message": {**chat, "text": "/start"}})
    assert "Send me a photo" in sent()[-1]
    handle({"message": {**chat, "photo": [{"file_id": "small"}, {"file_id": "big"}]}})
    assert "access code" in sent()[-1] and jobs.empty(), "a locked chat must not queue a check"
    handle({"message": {**chat, "text": "/unlock wrong"}})
    assert "does not match" in sent()[-1] and 42 not in unlocked
    handle({"message": {**chat, "text": "/unlock letmein"}})
    assert 42 in unlocked
    handle({"message": {**chat, "text": "/lang xx"}})
    assert "Choose one of" in sent()[-1]
    handle({"message": {**chat, "text": "/lang@SnapBot te"}})
    assert language[42] == "te", "a command may carry the bot's name"
    handle({"message": {**chat, "photo": [{"file_id": "small"}, {"file_id": "big"}]}})
    assert jobs.qsize() == 1
    chat_id, file_id, lang = jobs.get_nowait()
    assert (chat_id, file_id, lang) == (42, "big", "te"), "the largest photo size and the chosen language"
    run_job(chat_id, file_id, lang)
    method, fields, files = documents[0]
    name, data, ctype = files["document"]
    assert method == "sendDocument" and name == "safe-copy.png" and data.startswith(b"\x89PNG"), "the safe copy goes out as a PNG file"
    assert "Hidden:" in fields["caption"] and "->" in fields["caption"], "the caption says what was hidden and the before and after"
    handle({"message": {**chat, "document": {"file_id": "doc", "mime_type": "image/jpeg"}}})
    assert jobs.qsize() == 1, "an image sent as a file is checked too"
    jobs.get_nowait()
    handle({"message": {**chat, "photo": [{"file_id": "x"}]}})
    jobs.get_nowait()
    handle({"message": {**chat, "photo": [{"file_id": "y"}]}})
    assert "limit" in sent()[-1] and jobs.empty(), "a fourth photo within the hour is refused"
    handle({"message": {**chat, "document": {"file_id": "z", "mime_type": "application/pdf"}}})
    assert "Send me a photo" in sent()[-1]
    done = {"before": {"identity": 4, "home_location": 3}, "after": {"identity": 1}, "hidden": [{"label": "ID number"}],
            "safe": False, "unverified": True, "doubt": False}
    text = report("A summary.", done)
    assert "Who you are: exact -> broad" in text and "Where you live: specific -> nothing" in text and "not verified" in text
    assert "ID number" in text and "guarantee" in report("", {**done, "safe": True, "unverified": False})
    assert TOKEN not in " ".join(sent()), "the token never appears in a message"
    print("telegram bot ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
