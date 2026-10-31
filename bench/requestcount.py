"""Counts the HTTP requests the benchmark actually sends to the model API, with no estimates.

The counter hangs on the OpenAI client's own HTTP client, so a request is counted every time it goes out, including the
client's automatic retries after a 429 or a server error, which a count around meta._ask would miss. Each request is
labelled from what it carries:

    model   the "model" field of the request body
    role    "verifier" while a benchmark scene is being read before and after (see role()), else "agent": the attacker's
            reports and the agent's own text checks
    kind    attack (the first attack of a scene), attack_more (every later one: re-attacks and retries after a doubted
            report), transcribe (a literal read of a photo), link (linking clues across photos), caption (rewriting a caption)
    outcome the HTTP status of the answer, or "no_answer" for a request that timed out or failed before one came back

Nothing in a request body is stored: only those labels.
"""
import contextvars
import json
import threading
from collections import Counter
from contextlib import contextmanager

_role = contextvars.ContextVar("role", default="agent")
_scene = contextvars.ContextVar("scene", default="")


@contextmanager
def role(name: str, scene: str = ""):
    """Label the requests sent inside this block (in this thread) as made by `name`, for `scene`."""
    a, b = _role.set(name), _scene.set(scene or _scene.get())
    try:
        yield
    finally:
        _role.reset(a)
        _scene.reset(b)


def kind_of(body: dict) -> str:
    """What a request is for, judged from the first text of its first message."""
    from app import meta

    content = (body.get("messages") or [{}])[0].get("content")
    first = content if isinstance(content, str) else next((p.get("text", "") for p in content or [] if p.get("type") == "text"), "")
    for kind, text in (("attack", meta.ATTACK_PROMPT), ("transcribe", meta.TRANSCRIBE), ("link", meta.LINK_PROMPT),
                       ("caption", meta.REWRITE)):
        if first.startswith(text[:40]):
            return kind
    return "other"


class RequestCounter:
    """Counts requests by (scene, role, model, kind, outcome). Safe to use from the benchmark's worker threads."""

    def __init__(self):
        self.rows: Counter = Counter()
        self._lock = threading.Lock()
        self._attacked: set = set()  # scenes whose first attack request has gone out
        self._open: dict = {}  # id(request) -> row waiting for its answer

    def on_request(self, request) -> None:
        try:
            body = json.loads(request.content or b"{}")
        except ValueError:
            body = {}
        scene, who, kind = _scene.get(), _role.get(), kind_of(body)
        with self._lock:
            if kind == "attack":
                kind = "attack_more" if scene in self._attacked else "attack"
                self._attacked.add(scene)
            row = (scene, who, str(body.get("model", "?")), kind)
            self._open[id(request)] = row
            self.rows[row + ("no_answer",)] += 1

    def on_response(self, response) -> None:
        with self._lock:
            row = self._open.pop(id(response.request), None)
            if row is None:
                return
            self.rows[row + ("no_answer",)] -= 1
            self.rows[row + (str(response.status_code),)] += 1

    def install(self, client) -> None:
        """Attach to an OpenAI client; call once per client."""
        hooks = client._client.event_hooks
        client._client.event_hooks = {"request": [*hooks.get("request", []), self.on_request],
                                      "response": [*hooks.get("response", []), self.on_response]}

    # ---- reading the counts ----
    def total(self, **match) -> int:
        names = ("scene", "role", "model", "kind", "outcome")
        return sum(n for row, n in self.rows.items() if n and all(row[names.index(k)] == v for k, v in match.items()))

    def by(self, field: str, **match) -> dict:
        names = ("scene", "role", "model", "kind", "outcome")
        out: Counter = Counter()
        for row, n in self.rows.items():
            if n and all(row[names.index(k)] == v for k, v in match.items()):
                out[row[names.index(field)]] += n
        return dict(sorted(out.items()))

    def failed(self) -> int:
        return sum(n for row, n in self.rows.items() if n and not row[4].startswith("2"))

    def snapshot(self, scene: str | None = None) -> dict:
        match = {"scene": scene} if scene is not None else {}
        return {"total": self.total(**match), "failed": sum(n for row, n in self.rows.items()
                                                            if n and not row[4].startswith("2") and (scene is None or row[0] == scene)),
                "by_role": self.by("role", **match), "by_model": self.by("model", **match),
                "by_kind": self.by("kind", **match), "by_outcome": self.by("outcome", **match),
                "by_model_role": self._pairs(scene)}

    def _pairs(self, scene) -> dict:
        out: Counter = Counter()
        for row, n in self.rows.items():
            if n and (scene is None or row[0] == scene):
                out[f"{row[2]} / {row[1]}"] += n
        return dict(sorted(out.items()))

    def lines(self) -> list[str]:
        s = self.snapshot()
        out = ["| Requests actually sent | Count |", "|---|---|", f"| Total (including retries) | {s['total']} |",
               f"| Answered with an error or not at all | {s['failed']} |"]
        for title, key in (("By role", "by_role"), ("By model", "by_model"), ("By model and role", "by_model_role"),
                           ("By request type", "by_kind"), ("By outcome (HTTP status)", "by_outcome")):
            out += [f"| **{title}** | |"] + [f"| {k} | {n} |" for k, n in s[key].items()]
        return out


if __name__ == "__main__":
    class Req:
        def __init__(self, body):
            self.content = json.dumps(body).encode()

    class Rsp:
        def __init__(self, req, status):
            self.request, self.status_code = req, status

    from app import meta
    c = RequestCounter()
    attack = Req({"model": "m1", "messages": [{"content": [{"type": "text", "text": meta.ATTACK_PROMPT}]}]})
    read = Req({"model": "m2", "messages": [{"content": [{"type": "text", "text": meta.TRANSCRIBE}]}]})
    with role("verifier", "s1"):
        c.on_request(read), c.on_response(Rsp(read, 200))
    with role("agent", "s1"):
        for status in (429, 200):
            a = Req(json.loads(attack.content))
            c.on_request(a), c.on_response(Rsp(a, status))
        lost = Req(json.loads(attack.content))
        c.on_request(lost)  # never answered
    s = c.snapshot()
    assert s["total"] == 4 and s["failed"] == 2 and s["by_kind"] == {"attack": 1, "attack_more": 2, "transcribe": 1}
    assert s["by_role"] == {"agent": 3, "verifier": 1} and s["by_outcome"] == {"200": 2, "429": 1, "no_answer": 1}
    print("requestcount ok")
