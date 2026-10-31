"""Offline checks for the benchmark's API request counter (bench/requestcount.py). The model API is a stand-in HTTP
transport, so no key, no network and no quota are used.

Run: uv run python -m tests.test_requestcount
"""
import importlib
import json
import tempfile
from pathlib import Path

import openai

from app import meta
from bench import indiabench, requestcount


def mock_client(handler):
    """An OpenAI client whose HTTP traffic goes to `handler(request) -> (status, json)` instead of the network."""
    probe = openai.OpenAI(api_key="x")
    http = next(c for c in type(probe._client).__mro__ if not c.__module__.startswith("openai"))
    base = importlib.import_module(http.__module__.split(".")[0])  # httpx, or the fork the SDK uses
    transport = base.MockTransport(lambda req: _respond(base, handler, req))
    return openai.OpenAI(api_key="test", base_url="http://mock.invalid/v1", max_retries=2,
                         http_client=openai.DefaultHttpxClient(transport=transport))


def _respond(base, handler, req):
    status, body = handler(req)
    return base.Response(status, json=body)


def tool_reply(payload: dict) -> dict:
    call = {"id": "call_1", "type": "function", "function": {"name": "x", "arguments": json.dumps(payload)}}
    return {"id": "r", "object": "chat.completion", "created": 0, "model": "mock-model", "choices": [
        {"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": None, "tool_calls": [call]}}]}


def run_scene(scene_id: str, fail_first: bool = False):
    """Run one benchmark scene end to end against the stand-in API; return (record, counter)."""
    seen = {"attacks": 0, "failed": False}

    def handler(req):
        if fail_first and not seen["failed"]:
            seen["failed"] = True
            return 429, {"error": {"message": "slow down", "type": "rate_limit"}}
        body = json.loads(req.content)
        kind = requestcount.kind_of(body)
        if kind == "attack":
            seen["attacks"] += 1
            return 200, tool_reply(meta.MOCK_ATTACK if seen["attacks"] == 1 else meta.MOCK_CLEAN)
        assert kind == "transcribe", kind
        return 200, tool_reply({"texts": ["Tea 10", "Coffee 15"]})

    saved = (meta.open_client, meta.OPEN_MODEL, meta.OPEN_RPM, indiabench.COUNTER)
    counter = requestcount.RequestCounter()
    meta.open_client, meta.OPEN_MODEL, meta.OPEN_RPM, indiabench.COUNTER = mock_client(handler), "mock-model", 0, counter
    counter.install(meta.open_client)
    try:
        scene = next(s for s in json.loads((indiabench.ROOT / "scenes.json").read_text(encoding="utf-8")) if s["id"] == scene_id)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "images").mkdir()
            rec = indiabench.evaluate(scene, Path(tmp))
    finally:
        meta.open_client, meta.OPEN_MODEL, meta.OPEN_RPM, indiabench.COUNTER = saved
    return rec, counter


def test_counts_every_request_by_role_and_kind():
    rec, counter = run_scene("ctrl_tea_menu")
    snap = counter.snapshot()
    assert snap["total"] == sum(snap["by_outcome"].values()) and snap["failed"] == 0
    assert snap["by_role"].get("verifier") == 2, "the verifier reads the photo twice: before and after"
    assert snap["by_kind"].get("attack") == 1, "one first attack per scene"
    assert snap["by_kind"].get("attack_more", 0) == rec["attacks"] - 1, "later attacks are counted from the run itself"
    assert snap["by_model"] == {"mock-model": snap["total"]}
    assert rec["requests"] == counter.snapshot("ctrl_tea_menu"), "the record carries this scene's own counts"
    assert snap["by_role"]["agent"] == snap["by_kind"]["attack"] + snap["by_kind"].get("attack_more", 0) + \
        (snap["by_kind"]["transcribe"] - 2), "agent requests are the attacks plus its own text reads"


def test_retries_after_an_error_are_counted():
    rec, counter = run_scene("ctrl_tea_menu", fail_first=True)
    snap = counter.snapshot()
    assert snap["failed"] == 1 and snap["by_outcome"]["429"] == 1, "the 429 went out and is counted"
    clean, plain = run_scene("ctrl_tea_menu")[1].snapshot(), snap
    assert plain["total"] == clean["total"] + 1, "the retried request is one extra request on the wire"


def test_unanswered_requests_are_visible():
    c = requestcount.RequestCounter()

    class R:
        content = json.dumps({"model": "m", "messages": [{"content": "hi"}]}).encode()

    c.on_request(R())
    s = c.snapshot()
    assert s["total"] == 1 and s["failed"] == 1 and s["by_outcome"] == {"no_answer": 1}


def test_nothing_from_the_request_body_is_kept():
    _, counter = run_scene("ctrl_tea_menu")
    dump = json.dumps([list(k) for k in counter.rows])
    assert "data:image" not in dump and "red-teamer" not in dump


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
