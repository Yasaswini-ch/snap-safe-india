"""Offline checks for meta.KeyPool, which spreads calls over several API keys and moves on when one key runs out of quota.
The model API is a stand-in HTTP transport, so no key, no network and no quota are used.

Run: uv run python -m tests.test_keypool
"""
import importlib

import openai

from app import meta

QUOTA = {"error": {"code": 429, "message": "You exceeded your current quota. Generate content requests per day limit exceeded. "
                   "Please retry in 22h11m14.02s", "status": "RESOURCE_EXHAUSTED"}}
OK = {"id": "r", "object": "chat.completion", "created": 0, "model": "m", "choices": [
    {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "ok"}}]}


def pool(behaviour: dict[str, int]):
    """A KeyPool of stand-in clients. behaviour maps a key to the status it answers (200 or 429); calls are counted per key."""
    calls = {k: 0 for k in behaviour}
    probe = openai.OpenAI(api_key="x")
    http = next(c for c in type(probe._client).__mro__ if not c.__module__.startswith("openai"))
    base = importlib.import_module(http.__module__.split(".")[0])

    def make(key):
        def handler(req):
            calls[key] += 1
            return base.Response(behaviour[key], json=OK if behaviour[key] == 200 else QUOTA)
        return openai.OpenAI(api_key=key, base_url="http://mock.invalid/v1", max_retries=0,
                             http_client=openai.DefaultHttpxClient(transport=base.MockTransport(handler)))
    return meta.KeyPool(list(behaviour), make), calls


def ask(p, model="gemini-test"):
    return p.chat.completions.create(model=model, messages=[{"role": "user", "content": "hi"}])


def test_a_dry_key_hands_over_to_the_next():
    p, calls = pool({"k1": 429, "k2": 200})
    assert ask(p).choices[0].message.content == "ok"
    assert calls == {"k1": 1, "k2": 1}


def test_a_resting_key_is_not_asked_again():
    p, calls = pool({"k1": 429, "k2": 200})
    for _ in range(4):
        ask(p)  # the start key alternates, but k1 rests after its first 429
    assert calls["k1"] == 1 and calls["k2"] == 4


def test_calls_spread_over_healthy_keys():
    p, calls = pool({"k1": 200, "k2": 200, "k3": 200})
    for _ in range(6):
        ask(p)
    assert calls == {"k1": 2, "k2": 2, "k3": 2}


def test_all_keys_dry_raises_and_does_not_loop():
    p, calls = pool({"k1": 429, "k2": 429})
    for _ in range(2):
        try:
            ask(p)
            raise AssertionError("should have raised")
        except openai.RateLimitError:
            pass
    assert calls["k1"] + calls["k2"] <= 4  # a resting key is asked at most once more, by the last-resort path


def test_rest_is_per_model():
    p, calls = pool({"k1": 429, "k2": 200})
    ask(p, "model-a")
    before = calls["k1"]
    ask(p, "model-a"); ask(p, "model-a")
    assert calls["k1"] == before  # still resting for model-a
    p.start = 0
    ask(p, "model-b")
    assert calls["k1"] == before + 1  # its quota for model-b was never used up


def test_cooldown_reads_the_providers_delay():
    assert meta._cooldown(Exception("... 'retryDelay': '45s' ...")) == 45
    assert meta._cooldown(Exception("Please retry in 1m30s")) == 90
    assert meta._cooldown(Exception("Please retry in 22h11m14.02s")) == 21600  # capped at 6 hours
    assert meta._cooldown(Exception("Generate content requests per day limit")) == 3600
    assert meta._cooldown(Exception("slow down")) == 60


def test_one_key_still_works():
    p, calls = pool({"only": 200})
    assert ask(p).choices[0].message.content == "ok" and calls["only"] == 1


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
