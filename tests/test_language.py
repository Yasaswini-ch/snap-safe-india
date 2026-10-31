"""Offline checks for the report language (English, Telugu, Hindi). No API key and no network: the model, the Telegram
API and the server's upload path are replaced by stand-ins. All text here is made up.

Run: uv run python -m tests.test_language
"""
import asyncio
import io
import json
import re
from pathlib import Path

import numpy as np
from fastapi import UploadFile
from PIL import Image

from app import main, meta, telegram_bot

# Made-up report prose. Telugu and Hindi use conjuncts, vowel signs and the joiners that break naive string handling.
TELUGU = "ఈ ఫోటోలో మీ ఇంటి చిరునామా స్పష్టంగా కనిపిస్తోంది. శ్రీ సాయి మెడికల్స్ క్రమం‌ ప్రశ్న"
HINDI = "इस फ़ोटो में आपके घर का पता साफ़ दिखता है। श्री साई मेडिकल्स क्षत्रिय ज्ञान कार्य‍"
SAMPLES = {"te": TELUGU, "hi": HINDI}


def blank() -> np.ndarray:
    return np.full((64, 64, 3), 255, np.uint8)


def capture_prompts(fn):
    """Run fn with meta._ask replaced; return the prompt text of every request it made."""
    prompts, real_ask, real_client = [], meta._ask, meta.open_client

    def fake_ask(messages, schema, name, private, effort="", model=""):
        parts = messages[0]["content"]
        prompts.append(parts if isinstance(parts, str) else " ".join(p.get("text", "") for p in parts))
        return {"clues": [], "inferences": [], "summary": "", "links": []}

    meta._ask, meta.open_client = fake_ask, object()
    try:
        fn()
    finally:
        meta._ask, meta.open_client = real_ask, real_client
    return prompts


def test_language_codes():
    assert meta.LANGS == {"en": "English", "te": "Telugu", "hi": "Hindi"}
    assert meta._language("en") == ""
    for code, name in (("te", "Telugu"), ("hi", "Hindi")):
        note = meta._language(code)
        assert name in note and "summary" in note and "observation" in note and "reasoning" in note
        assert "label" in note, "labels stay English because they are matched for the edits"


def test_unknown_language_is_english():
    for bad in ("", "xx", "TE", "hindi", "te ", "../te", "తెలుగు", "ta"):
        assert meta._language(bad) == "", f"{bad!r} must add no language note"
    base = capture_prompts(lambda: meta.attack([blank()], private=True))[0]
    for bad in ("xx", "", "ta"):
        assert capture_prompts(lambda: meta.attack([blank()], private=True, lang=bad))[0] == base, bad


def test_prompt_carries_language():
    base = capture_prompts(lambda: meta.attack([blank()], private=True, lang="en"))[0]
    assert meta.LANG_NOTE.split("{")[0].strip() not in base, "English adds no language note"
    for code, name in (("te", "Telugu"), ("hi", "Hindi")):
        p = capture_prompts(lambda: meta.attack([blank()], private=True, lang=code))[0]
        assert p.count(meta._language(code)) == 1 and p.replace(meta._language(code), "", 1) == base,             "the note is the only difference from the English prompt"
        assert f"in {name}" in p
        assert meta._language("hi" if code == "te" else "te") not in p  # the region note names both scripts, so compare notes


def test_large_account_keeps_language():
    imgs = [np.full((64, 64, 3), i * 20, np.uint8) for i in range(meta.MAX_TOGETHER + 1)]
    meta._one_by_one.clear()
    prompts = capture_prompts(lambda: meta._attack_large(imgs, True, "", [""] * len(imgs), False, "hi"))
    assert prompts and all("in Hindi" in p for p in prompts), "every per-photo request is told the language"


def test_unicode_survives_normalize_and_json():
    for code, text in SAMPLES.items():
        graph = {"clues": [{"id": "c1", "box": [0, 0, 500, 500], "label": "street sign", "observation": text,
                            "kind": "text", "legibility": "clear", "suggested": "replace", "removal_impact": "low"}],
                 "inferences": [{"category": "home_location", "reasoning": text, "ways": [{"clues": ["c1"], "level": 3}]}],
                 "summary": text}
        out = meta.normalize(graph)
        assert out["summary"] == text and out["clues"][0]["observation"] == text, code
        assert out["inferences"][0]["reasoning"] == text
        for ensure in (True, False):  # the server escapes, the sample files do not
            wire = json.dumps(out, ensure_ascii=ensure)
            assert json.loads(wire.encode("utf-8").decode("utf-8")) == out
        assert "‌" in TELUGU and "‍" in HINDI, "the test text really holds the joiners"


def run_endpoint(lang_field):
    """Post one photo to /api/run with the model replaced; return the language the attacker was given."""
    seen = []
    real = (meta.attack, meta.read_text, main.PRIVATE, main.LIVE_CODE)

    def fake_attack(imgs, private=False, lang="en", **kw):
        seen.append(lang)
        return meta.mock_attacker()(imgs) if len(seen) == 1 else meta.normalize(meta.MOCK_CLEAN)

    meta.attack, meta.read_text, main.PRIVATE, main.LIVE_CODE = fake_attack, lambda *a, **k: [], True, None
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(buf, "PNG")

    class Req:
        headers, client = {}, type("c", (), {"host": "127.0.0.1"})()

    async def go():
        photo = UploadFile(io.BytesIO(buf.getvalue()), filename="a.png")
        kw = {} if lang_field is None else {"lang": lang_field}
        rsp = await main.run(Req(), photos=[photo], private=True, code="", caption="", captions="", **kw)
        return [json.loads(line) async for line in rsp.body_iterator if line.strip()]

    try:
        events = asyncio.run(go())
    finally:
        meta.attack, meta.read_text, main.PRIVATE, main.LIVE_CODE = real
    assert events[-1]["type"] == "done", events[-1]
    return set(seen)


def test_server_language_plumbing():
    assert run_endpoint("te") == {"te"} and run_endpoint("hi") == {"hi"} and run_endpoint("en") == {"en"}
    assert run_endpoint("xx") == {"en"} and run_endpoint("") == {"en"}, "unknown codes fall back to English"
    assert run_endpoint("TE") == {"en"}, "codes are case sensitive; the page only sends lower case"


def test_page_offers_exactly_the_server_languages():
    html = (Path(main.__file__).parent.parent / "static" / "index.html").read_text(encoding="utf-8")
    select = re.search(r'<select id="lang">(.*?)</select>', html, re.S).group(1)
    assert set(re.findall(r'value="(\w+)"', select)) == set(meta.LANGS)
    assert 'charset="utf-8"' in html and 'body.append("lang"' in html
    assert "తెలుగు" in select and "हिन्दी" in select, "the language names are written in their own scripts"


def test_bot_language_command_and_report():
    bot = telegram_bot
    sent, jobs_before = [], bot.jobs.qsize()
    real = (bot._post_json, bot.CODE, bot.language.copy(), bot._post_form)
    bot._post_json = lambda method, params, timeout=70: (sent.append(params) or {"ok": True, "result": {"message_id": 1}})
    bot.CODE = None
    try:
        chat = {"chat": {"id": 7}}
        for text, want in (("/lang te", "te"), ("/lang hi", "hi"), ("/lang en", "en"), ("/lang@SnapBot hi", "hi")):
            bot.handle({"message": {**chat, "text": text}})
            assert bot.language[7] == want, text
        for text in ("/lang", "/lang xx", "/lang tamil"):
            bot.language[7] = "hi"
            bot.handle({"message": {**chat, "text": text}})
            assert bot.language[7] == "hi", f"{text!r} must not change the language"
            assert "Choose one of" in sent[-1]["text"]
        bot.handle({"message": {**chat, "text": "/lang HI"}})
        assert bot.language[7] == "hi" and "Choose one of" in sent[-1]["text"], "upper case is refused, not guessed"
        bot.language.pop(7)
        bot.handle({"message": {**chat, "photo": [{"file_id": "p"}]}})
        assert bot.jobs.get_nowait()[2] == "en", "a chat that never chose a language gets English"
        assert bot.jobs.qsize() == jobs_before
    finally:
        bot._post_json, bot.CODE, bot._post_form = real[0], real[1], real[3]
        bot.language.clear()
        bot.language.update(real[2])
        bot.recent.clear()

    done = {"before": {"home_location": 4}, "after": {}, "hidden": [{"label": "street sign"}], "safe": True,
            "unverified": False, "doubt": False}
    for text in SAMPLES.values():
        report = bot.report(text, done)
        assert report.startswith(text), "the model's Telugu or Hindi summary leads the reply"
        assert "Where you live: exact -> nothing" in report, "the frame around it is English"
        # the multipart upload encodes the caption as UTF-8
        captured = {}
        bot._post_form = lambda m, fields, files, timeout=120: (captured.update(fields) or {"ok": True})
        try:
            bot.send_document(7, b"\x89PNG", "safe-copy.png", report)
        finally:
            bot._post_form = real[3]
        assert captured["caption"] == report[:1024]


def test_post_form_body_is_utf8():
    import urllib.request

    sent = {}

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    real = urllib.request.urlopen
    urllib.request.urlopen = lambda req, timeout=0: (sent.update(body=req.data) or Resp())
    try:
        telegram_bot._post_form("sendDocument", {"chat_id": "1", "caption": TELUGU + "\n" + HINDI},
                                {"document": ("safe-copy.png", b"\x89PNG", "image/png")})
    finally:
        urllib.request.urlopen = real
    body = sent["body"]
    assert TELUGU.encode("utf-8") in body and HINDI.encode("utf-8") in body, "UTF-8 bytes on the wire, no mojibake"


def test_long_telugu_report_goes_out_as_a_message():
    """A caption over Telegram's 1024 characters is sent as a message after a short one, and nothing is cut mid-text
    below the 4096 limit."""
    bot = telegram_bot
    jobs_saved, real = bot.jobs.qsize(), (bot.say, bot.send_document, bot.download, bot.working)
    out = {"messages": [], "docs": []}
    done = {"before": {"identity": 4}, "after": {}, "hidden": [{"label": "ID card"}], "safe": True, "unverified": False,
            "doubt": False, "images": [__import__("base64").b64encode(b"\x89PNGfake").decode()]}
    long_summary = " ".join([TELUGU] * 14)
    assert len(bot.report(long_summary, done)) > 1024 and len(bot.report(long_summary, done)) < 4096

    class Agent:
        @staticmethod
        def run(*a, **k):
            yield {"type": "attack", "graph": {"summary": long_summary}}
            yield {"type": "done", **done}

    saved_agent, saved_load = bot.agent, bot.pipeline.load_image
    bot.say = lambda chat, text: out["messages"].append(text)
    bot.send_document = lambda chat, data, name, caption: out["docs"].append(caption)
    bot.download = lambda file_id: b"x"
    bot.agent, bot.pipeline.load_image = Agent, lambda data, side: (blank(), {})
    try:
        bot.run_job(9, "f", "te")
    finally:
        bot.say, bot.send_document, bot.download, bot.working = real
        bot.agent, bot.pipeline.load_image = saved_agent, saved_load
    assert out["docs"] == ["Your safe copy: no EXIF or GPS data."]
    assert any(m.startswith(TELUGU[:20]) and "->" in m for m in out["messages"]), "the full Telugu report is sent as a message"
    assert bot.jobs.qsize() == jobs_saved


def test_mock_mode_ignores_language():
    """Without a key the placeholder report is English whatever was asked. Not a bug, but the page must not promise more."""
    real = meta.open_client
    meta.open_client = None
    try:
        assert meta.attack([blank()], private=True, lang="te")["summary"] == meta.MOCK_ATTACK["summary"]
    finally:
        meta.open_client = real


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {str(e)[:300].encode('ascii', 'replace').decode()}")
    print(f"{len(tests) - failed} of {len(tests)} passed")
    raise SystemExit(1 if failed else 0)
