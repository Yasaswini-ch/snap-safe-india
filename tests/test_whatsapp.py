"""Offline checks for the WhatsApp front end (app/whatsapp.py). The Graph API is replaced by stand-in functions and the
agent uses its placeholder attacker, so no token, no network and no model quota are used.

Run: uv run python -m tests.test_whatsapp
"""
import asyncio
import base64
import hashlib
import hmac
import io
import json

import numpy as np
from fastapi import HTTPException
from starlette.requests import Request

from app import meta, pipeline, whatsapp as wa

SECRET = "app-secret"


class Graph:
    """Records every call the module makes to the Graph API and answers the few it needs."""

    def __init__(self, photo: bytes = b""):
        self.sent, self.uploads, self.photo = [], [], photo

    def json(self, method, url, payload=None, timeout=30):
        if method == "GET":  # media info
            return {"url": "http://media.invalid/file", "file_size": len(self.photo)}
        self.sent.append(payload)
        return {"messages": [{"id": "wamid.out"}]}

    def form(self, url, fields, name, data, ctype, timeout=120):
        self.uploads.append((name, data, ctype))
        return {"id": "media-out-1"}

    def bytes(self, url, timeout=60):
        return self.photo


def setup(photo: bytes = b"") -> Graph:
    g = Graph(photo)
    wa._json, wa._form, wa._bytes = g.json, g.form, g.bytes
    wa.TOKEN, wa.PHONE_ID, wa.VERIFY, wa.SECRET, wa.CODE = "t", "123", "verify-me", SECRET, None
    wa.language.clear(); wa.style.clear(); wa.recent.clear(); wa.seen.clear(); wa.unlocked.clear()
    meta.open_client = None  # the placeholder attacker
    return g


def text(body: str, sender="9199", mid=None) -> dict:
    return {"from": sender, "id": mid or f"wamid.{abs(hash((body, sender)))}", "type": "text", "text": {"body": body}}


def photo_bytes() -> bytes:
    return pipeline.encode_png(np.random.default_rng(0).integers(0, 256, (240, 320, 3), dtype=np.uint8))


def request(method="GET", query=b"", body=b"", headers=None) -> Request:
    sent = {"done": False}

    async def receive():
        if sent["done"]:
            return {"type": "http.disconnect"}
        sent["done"] = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {"type": "http", "method": method, "path": "/whatsapp/webhook", "query_string": query,
             "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]}
    return Request(scope, receive)


def signed(body: bytes) -> dict:
    return {"x-hub-signature-256": "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()}


def test_signature_checks_the_raw_body():
    setup()
    body = b'{"a": 1}'
    assert wa.valid_signature(body, signed(body)["x-hub-signature-256"])
    assert not wa.valid_signature(body + b" ", signed(body)["x-hub-signature-256"])
    assert not wa.valid_signature(body, "") and not wa.valid_signature(body, "sha256=00")
    wa.SECRET = ""
    assert not wa.valid_signature(body, signed(body)["x-hub-signature-256"]), "no app secret set: nothing is trusted"


def test_webhook_verification():
    setup()
    ok = wa.verify(request(query=b"hub.mode=subscribe&hub.verify_token=verify-me&hub.challenge=777"))
    assert ok.body == b"777"
    for bad in (b"hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=1", b"hub.mode=other&hub.verify_token=verify-me"):
        try:
            wa.verify(request(query=bad))
            raise AssertionError("accepted a bad verification")
        except HTTPException as e:
            assert e.status_code == 403
    wa.TOKEN = ""
    try:
        wa.verify(request(query=b"hub.mode=subscribe&hub.verify_token=verify-me"))
        raise AssertionError("answered while unconfigured")
    except HTTPException as e:
        assert e.status_code == 404


def test_receive_rejects_unsigned_calls_and_accepts_signed_ones():
    g = setup()
    body = json.dumps({"entry": [{"changes": [{"value": {"messages": [text("hi")]}}]}]}).encode()
    try:
        asyncio.run(wa.receive(request("POST", body=body, headers={"x-hub-signature-256": "sha256=bad"})))
        raise AssertionError("accepted a bad signature")
    except HTTPException as e:
        assert e.status_code == 403
    assert not g.sent
    assert asyncio.run(wa.receive(request("POST", body=body, headers=signed(body)))) == {"ok": True}
    assert g.sent and "photo" in g.sent[0]["text"]["body"].lower()


def test_commands():
    g = setup()
    wa.handle_message(text("lang te", mid="1"))
    assert wa.language["9199"] == "te" and "Telugu" in g.sent[-1]["text"]["body"]
    wa.handle_message(text("lang xx", mid="2"))
    assert wa.language["9199"] == "te" and "Choose one of" in g.sent[-1]["text"]["body"]
    wa.handle_message(text("/style clean", mid="3"))
    assert wa.style["9199"] == "clean"
    wa.handle_message(text("style glitter", mid="4"))
    assert wa.style["9199"] == "clean" and "clean or pixelate" in g.sent[-1]["text"]["body"]
    wa.handle_message(text("unlock nope", mid="5"))
    assert g.sent[-1]["text"]["body"] == "That code does not match."


def test_repeated_webhook_is_handled_once():
    g = setup()
    wa.handle_message(text("hi", mid="same"))
    wa.handle_message(text("hi", mid="same"))
    assert len(g.sent) == 1


def test_a_photo_gets_a_cleaned_copy_and_a_report():
    png = photo_bytes()
    g = setup(png)
    wa.run_job("9199", "media-in-1", "en", "")
    assert g.uploads and g.uploads[0][0] == "safe-copy.png" and g.uploads[0][2] == "image/png"
    out, _ = pipeline.load_image(g.uploads[0][1])  # a real PNG
    assert out.shape[:2] == (240, 320)
    doc = [m for m in g.sent if m.get("type") == "document"][0]
    assert doc["document"]["id"] == "media-out-1" and doc["document"]["filename"] == "safe-copy.png"
    assert len(doc["document"]["caption"]) <= 1024
    assert "to" in doc and doc["to"] == "9199"
    assert g.sent[0]["text"]["body"].startswith("Reading your photo")


def test_a_file_that_is_not_an_image_is_refused_kindly():
    g = setup(b"this is not an image")
    wa.run_job("9199", "media-in-2", "en", "")
    assert not g.uploads and "could not open" in g.sent[-1]["text"]["body"]


def test_access_code_and_hourly_limit():
    g = setup()
    wa.CODE = "Secret1"
    wa.handle_message({"from": "9199", "id": "p1", "type": "image", "image": {"id": "m1"}})
    assert "unlock" in g.sent[-1]["text"]["body"] and wa.jobs.empty()
    wa.handle_message(text("unlock secret1", mid="u1"))
    assert "9199" in wa.unlocked
    wa.CODE = None
    wa.PER_HOUR = 2
    wa._worker.append(object())  # no background thread in this check: the jobs just queue up
    for i in range(3):
        wa.handle_message({"from": "9199", "id": f"q{i}", "type": "image", "image": {"id": f"m{i}"}})
    assert wa.jobs.qsize() == 2 and "limit of 2" in g.sent[-1]["text"]["body"]
    while not wa.jobs.empty():
        wa.jobs.get()
    wa._worker.clear()
    wa.PER_HOUR = 3


def test_documents_count_only_when_they_are_images():
    g = setup()
    wa._worker.append(object())
    wa.handle_message({"from": "9199", "id": "d1", "type": "document", "document": {"id": "x", "mime_type": "application/pdf"}})
    assert wa.jobs.empty() and "Send me a photo" in g.sent[-1]["text"]["body"]
    wa.handle_message({"from": "9199", "id": "d2", "type": "document", "document": {"id": "y", "mime_type": "image/jpeg"}})
    assert wa.jobs.qsize() == 1
    wa.jobs.get()
    wa._worker.clear()


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {str(e)[:300]}")
    print(f"{len(tests) - failed} of {len(tests)} passed")
    raise SystemExit(1 if failed else 0)
