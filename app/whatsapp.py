"""WhatsApp front end for the agent, on the WhatsApp Cloud API (Meta). Message the number a photo (best as a document, so
WhatsApp keeps its full quality) and get the cleaned copy back with what was hidden and what a stranger could still learn.
Same agent, model settings and run limits as the Telegram bot; the report text is shared.

It is a webhook, so it lives inside the web app: Meta calls POST /whatsapp/webhook with each incoming message and the app
answers through the Graph API. Nothing runs, and the two routes answer 404, until the settings below are present.
Standard library only for the network, so it adds no dependency. Setup: docs/whatsapp.md.

Settings: WHATSAPP_TOKEN (access token), WHATSAPP_PHONE_ID (the number's id), WHATSAPP_VERIFY_TOKEN (any string you choose,
typed again in Meta's webhook form), WHATSAPP_APP_SECRET (the app's secret: every webhook call must carry a valid signature).
Self-check, no token and no network:  uv run python -m tests.test_whatsapp
"""
import base64
import functools
import hashlib
import hmac
import json
import logging
import os
import queue
import threading
import time
import urllib.error
import urllib.request
import uuid

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool

from . import agent, meta, pipeline
from .telegram_bot import report

TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
VERIFY = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
VERSION = os.environ.get("WHATSAPP_API_VERSION", "v21.0")
CODE = os.environ.get("LIVE_CODE") or None  # optional, as on the web page: send "unlock <code>" first
PER_HOUR = int(os.environ.get("BOT_RUNS_PER_HOUR", "3"))  # photos per sender per hour: the model's quota is the limit
MAX_SIDE = 2048
MAX_BYTES = 20 * 1024 * 1024
LANGUAGES = "en (English), te (Telugu), hi (Hindi)"
HELP = ("Send me a photo before you post it. I look at it the way a stranger would, hide only what gives you away "
        "(ID numbers, number plates, addresses, UPI IDs, labels), and check again. A check takes a minute or two.\n\n"
        "Send it as a document (attach, then Document) to keep its full quality.\n\n"
        "lang en|te|hi  the language of my report (" + LANGUAGES + ")\n"
        "style clean|pixelate  how hidden text is covered: matched to the colour around it, or pixelated\n"
        "help  this message\n\n"
        "Your photo is only held in memory while it is checked, and is sent to the model's host to find the clues.")

log = logging.getLogger("whatsapp")
router = APIRouter(prefix="/whatsapp")
jobs: queue.Queue = queue.Queue()  # (sender, media id, language, style): one check at a time
working = threading.Event()
unlocked: set[str] = set()
language: dict[str, str] = {}
style: dict[str, str] = {}
recent: dict[str, list[float]] = {}
seen: dict[str, None] = {}  # message ids already handled: WhatsApp repeats a webhook it thinks was not answered
_lock = threading.Lock()
_worker: list[threading.Thread] = []


def configured() -> bool:
    return bool(TOKEN and PHONE_ID and VERIFY)


# The network layer: three small functions, so the self-check can replace them. Errors never carry the token.
def _request(req: urllib.request.Request, timeout: float):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:  # Graph explains 4xx errors in a JSON body
        body = json.loads(e.read() or b"{}")
        raise RuntimeError(f"WhatsApp API error {e.code}: {(body.get('error') or {}).get('message', 'no message')}") from None


def _json(method: str, url: str, payload: dict | None = None, timeout: float = 30) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.loads(_request(req, timeout) or b"{}")


def _form(url: str, fields: dict, name: str, data: bytes, ctype: str, timeout: float = 120) -> dict:
    boundary = uuid.uuid4().hex
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                 f"Content-Type: {ctype}\r\n\r\n".encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=b"".join(parts), headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.loads(_request(req, timeout) or b"{}")


def _bytes(url: str, timeout: float = 60) -> bytes:
    return _request(urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"}), timeout)[:MAX_BYTES + 1]


def _graph(path: str) -> str:
    return f"https://graph.facebook.com/{VERSION}/{path}"


def say(to: str, text: str) -> None:
    _json("POST", _graph(f"{PHONE_ID}/messages"), {"messaging_product": "whatsapp", "to": to, "type": "text",
                                                    "text": {"body": text[:4096]}})


def send_document(to: str, data: bytes, name: str, caption: str) -> None:
    media = _form(_graph(f"{PHONE_ID}/media"), {"messaging_product": "whatsapp", "type": "image/png"}, name, data, "image/png")
    _json("POST", _graph(f"{PHONE_ID}/messages"), {"messaging_product": "whatsapp", "to": to, "type": "document",
                                                    "document": {"id": media["id"], "filename": name, "caption": caption[:1024]}})


def download(media_id: str) -> bytes:
    info = _json("GET", _graph(media_id))
    if info.get("file_size", 0) > MAX_BYTES:
        raise ValueError("file too large")
    data = _bytes(info["url"])
    if len(data) > MAX_BYTES:
        raise ValueError("file too large")
    return data


def run_job(to: str, media_id: str, lang: str, edit_style: str) -> None:
    say(to, "Reading your photo. A check takes a minute or two.")
    try:
        img, _ = pipeline.load_image(download(media_id), MAX_SIDE)
    except Exception as e:
        log.warning("could not open a photo: %s", type(e).__name__)
        say(to, "I could not open that file. Send a JPEG, PNG or WebP photo, up to 20 MB.")
        return
    private = meta.open_client is not None
    attack = functools.partial(meta.attack, private=True, lang=lang) if private else meta.mock_attacker()
    read = functools.partial(meta.read_text, private=True, effort=meta.ATTACK_EFFORT) if private else None
    summary, done = "", None
    for event in agent.run([img], attack=attack, private=True, read=read, style=edit_style):
        if event["type"] == "attack" and not summary:
            summary = event["graph"].get("summary", "")
        elif event["type"] == "done":
            done = event
    png = base64.b64decode(done["images"][0])
    text = report(summary, done)
    if len(text) <= 1024:
        send_document(to, png, "safe-copy.png", text)
    else:
        send_document(to, png, "safe-copy.png", "Your safe copy: no EXIF or GPS data.")
        say(to, text)


def worker() -> None:
    while True:
        to, media_id, lang, edit_style = jobs.get()
        working.set()
        try:
            run_job(to, media_id, lang, edit_style)
        except Exception as e:
            log.exception("check failed")
            try:
                say(to, "The check hit an error before it finished (" + type(e).__name__ + "). Try again in a minute.")
            except Exception:
                pass
        finally:
            working.clear()


def allow(sender: str) -> bool:
    now = time.time()
    with _lock:
        runs = [t for t in recent.get(sender, []) if now - t < 3600]
        if len(runs) >= PER_HOUR:
            recent[sender] = runs
            return False
        recent[sender] = runs + [now]
        return True


def valid_signature(body: bytes, header: str) -> bool:
    """Meta signs every webhook call with the app secret: 'sha256=' and the HMAC-SHA256 of the raw body."""
    if not SECRET:
        return False
    expected = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.encode(), (header or "").encode())


def handle_message(msg: dict) -> None:
    sender = msg.get("from")
    if not sender or msg.get("id") in seen:
        return
    with _lock:
        seen[msg.get("id", "")] = None
        while len(seen) > 1000:
            seen.pop(next(iter(seen)))
    kind = msg.get("type")
    if kind == "text":
        word, _, arg = (msg["text"].get("body") or "").strip().lstrip("/").partition(" ")
        word, arg = word.lower(), arg.strip().lower()
        if word in ("hi", "hello", "hey", "start", "help", "menu"):
            say(sender, HELP)
        elif word == "lang":
            if arg in meta.LANGS:
                language[sender] = arg
                say(sender, f"Reports will be in {meta.LANGS[arg]}. The edits are the same.")
            else:
                say(sender, "Choose one of: " + LANGUAGES + ". For example: lang te")
        elif word == "style":
            if arg in ("clean", "pixelate"):
                style[sender] = arg
                say(sender, "Hidden text will be " + ("covered with the colour around it where that is plain, and pixelated "
                                                       "elsewhere." if arg == "clean" else "pixelated."))
            else:
                say(sender, "Choose clean or pixelate. For example: style clean")
        elif word == "unlock":
            if CODE and hmac.compare_digest(arg.encode(), CODE.lower().encode()):
                unlocked.add(sender)
                say(sender, "Unlocked. Send me a photo.")
            else:
                say(sender, "That code does not match.")
        else:
            say(sender, "Send me a photo and I will check it. Send help to see how.")
        return
    media_id = None
    if kind == "image":
        media_id = (msg.get("image") or {}).get("id")
    elif kind == "document" and ((msg.get("document") or {}).get("mime_type") or "").startswith("image/"):
        media_id = msg["document"].get("id")
    if not media_id:
        say(sender, "Send me a photo and I will check it. Send help to see how.")
        return
    if CODE and sender not in unlocked:
        say(sender, "Send unlock followed by the access code first. Ask the team for it.")
        return
    if not allow(sender):
        say(sender, f"That is the limit of {PER_HOUR} photos an hour for this number. Try again later.")
        return
    if not _worker:
        thread = threading.Thread(target=worker, daemon=True)
        _worker.append(thread)
        thread.start()
    ahead = jobs.qsize() + (1 if working.is_set() else 0)
    jobs.put((sender, media_id, language.get(sender, "en"), style.get(sender, "")))
    if ahead:
        say(sender, f"Got it. {ahead} photo{'s' if ahead != 1 else ''} ahead of yours.")


def handle(payload: dict) -> None:
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            for msg in (change.get("value") or {}).get("messages") or []:
                try:
                    handle_message(msg)
                except Exception:
                    log.exception("could not handle a message")


@router.get("/webhook")
def verify(request: Request):
    """Meta's one-time check when the webhook URL is saved: echo the challenge if the verify token matches."""
    q = request.query_params
    if not configured():
        raise HTTPException(404)
    if q.get("hub.mode") != "subscribe" or not hmac.compare_digest(q.get("hub.verify_token", "").encode(), VERIFY.encode()):
        raise HTTPException(403, "Verification failed")
    return Response(q.get("hub.challenge", ""), media_type="text/plain")


@router.post("/webhook")
async def receive(request: Request):
    if not configured():
        raise HTTPException(404)
    body = await request.body()
    if not valid_signature(body, request.headers.get("x-hub-signature-256", "")):
        raise HTTPException(403, "Bad signature")
    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(400, "Not JSON") from None
    await run_in_threadpool(handle, payload)
    return {"ok": True}
