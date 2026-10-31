"""Indian benchmark: rendered scenes with planted fictional secrets, scored by whether those secrets are still legible.

Ground truth is the planted strings. A verifier pass transcribes every readable text in
the original and in the cleaned photo; a secret counts only if it was legible in the original. The agent runs in
private mode, so the attacker is whatever OPEN_MODEL is (Gemma 4 in this fork). Regions come from REGION, so running
once with REGION=in and once with REGION=global shows what the India pack adds.

Usage: REGION=in uv run --env-file .env python -m bench.indiabench [--tag in] [--workers 3] [--only id,id] [--all] [--verifier model] [--force]
Runs the five core scenes; --all runs all ten. Scenes already scored in the results folder are reused, so a later --all run adds the rest
and the summary covers every scene. --verifier reads the before and after photos with another model (independent, and it spares the quota).
Scenes: uv run python -m bench.india.make_scenes
"""
import argparse
import base64
import functools
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from app import agent, meta, pipeline
from bench import requestcount

ROOT = Path(__file__).parent / "india"
IMAGES = ROOT / "images"
CHANGED = 8  # per-channel difference that counts as a changed pixel; ignores resampling noise
PRINTED_MIN = 6  # shorter secrets ("Reddy", "Teja") collide with ordinary words in the attacker's prose


def norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def legible(secrets: list[str], texts: list[str]) -> list[str]:
    """The secrets still readable in a transcription: compared without case, spaces or punctuation."""
    blob = norm(" ".join(texts))
    return [s for s in secrets if norm(s) in blob]


def changed(a: np.ndarray, b: np.ndarray) -> float:
    """Share of pixels that differ between the original and the result."""
    return float((np.abs(a.astype(int) - b.astype(int)) > CHANGED).any(-1).mean())


def attacker_text(graph: dict) -> str:
    """Everything the attacker wrote in a report, to check it never echoes a planted value."""
    return " ".join([graph["summary"], *(f"{c['label']} {c['observation']}" for c in graph["clues"]),
                     *(i["reasoning"] for i in graph["inferences"])])


def pct(a, b) -> str:
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "n/a"


def with_parts(secrets: list[str]) -> list[str]:
    """A name or place written in words also counts word by word (4+ letters): a half-hidden name is still a leak."""
    out = list(secrets)
    for s in secrets:
        words = s.split()
        if len(words) > 1 and all(w.isalpha() for w in words):
            out += [w for w in words if len(w) >= 4 and w not in out]
    return out


VERIFIER = ""  # --verifier: the model that reads the before and after photos
SCENE_SET = ""  # --set: a scene set other than the rendered scenes
COUNTER = requestcount.RequestCounter()  # every request actually sent to the model API in this run (bench/requestcount.py)


def labelled(fn, who: str, scene: str):
    """fn, with the requests it sends counted as `who` for `scene`. The label is set inside the call, because the agent
    runs some of its calls in worker threads, which do not inherit it."""
    def run(*a, **k):
        with requestcount.role(who, scene):
            return fn(*a, **k)
    return run


def evaluate(scene: dict, out: Path) -> dict:
    img, _ = pipeline.load_image((IMAGES / f"{scene['id']}.jpg").read_bytes())
    secrets = with_parts(scene["secrets"])
    rec = {"id": scene["id"], "kind": scene["kind"], "secrets": secrets, "expect": scene["expect"]}
    sid = scene["id"]
    verify = labelled(functools.partial(meta.read_text, private=True, model=VERIFIER), "verifier", sid)
    rec["verified"] = legible(secrets, verify(img))
    t = time.time()
    events = list(agent.run([img], attack=labelled(functools.partial(meta.attack, private=True), "agent", sid),
                            private=True, read=labelled(functools.partial(meta.read_text, private=True), "agent", sid)))
    rec["seconds"] = round(time.time() - t, 1)
    rec["model"], rec["verifier"] = meta.OPEN_MODEL, VERIFIER or meta.OPEN_MODEL  # who attacked and who read the photos
    attacks = [e for e in events if e["type"] == "attack"]
    done = events[-1]
    rec["exposure_before"], rec["exposure_after"], rec["safe"] = attacks[0]["exposure"], done["after"], done["safe"]
    rec["attacks"] = len(attacks)
    check = next((e for e in events if e["type"] == "textcheck"), None)
    rec["textcheck_found"] = sorted(check["found"]) if check else []
    rec["edits"] = [f"{d['action']}:{d['label']}:{d['mask']}" for e in events if e["type"] == "edits"
                    for d in e["edits"]]
    said = [attacker_text(a["graph"]) for a in attacks]
    rec["values_printed"] = legible([s for s in rec["verified"] if len(norm(s)) >= PRINTED_MIN], said)
    ours = np.asarray(Image.open(io.BytesIO(base64.b64decode(done["images"][0]))).convert("RGB"))
    rec["survived"] = legible(rec["verified"], verify(ours))
    rec["changed"] = round(changed(img, ours), 4)
    rec["requests"] = COUNTER.snapshot(sid)  # counted, not estimated: includes retries and every extra attack round
    Image.fromarray(ours).save(out / "images" / f"{scene['id']}_after.jpg", quality=88)
    return rec


def run_scene(scene: dict, out: Path, force: bool) -> dict:
    path = out / "scenes" / f"{scene['id']}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        rec = evaluate(scene, out)
    except Exception as e:
        rec = {"id": scene["id"], "kind": scene["kind"], "error": f"{type(e).__name__}: {str(e)[:200]}"}
    else:
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{scene['id']}: {'error ' + rec['error'] if 'error' in rec else 'ok'}", flush=True)
    return rec


def summarize(recs: list[dict], tag: str) -> str:
    ok = [r for r in recs if "error" not in r]
    leaky = [r for r in ok if r["kind"] == "leak"]
    controls = [r for r in ok if r["kind"] == "control"]
    worst = lambda e: max(e.values(), default=0)  # noqa: E731
    verified = sum(len(r["verified"]) for r in ok)
    printable = sum(len([s for s in r["verified"] if len(norm(s)) >= PRINTED_MIN]) for r in ok)
    with_secrets = [r for r in leaky if r["verified"]]
    expecting = [r for r in leaky if r["expect"]]
    hit = sum(set(r["expect"]) <= set(r["textcheck_found"]) for r in expecting)
    mean = lambda xs: sum(xs) / len(xs) if xs else 0  # noqa: E731
    lines = [
        f"# Indian benchmark results ({time.strftime('%Y-%m-%d')}, REGION={tag}, model {meta.OPEN_MODEL})", "",
        f"{len(ok)} scenes scored ({len(leaky)} leak, {len(controls)} control), {len(recs) - len(ok)} errors. "
        f"{verified} planted secrets were legible in the originals and are the ground truth below.", "",
        (f"Photograph-like images supplied by the team (set '{SCENE_SET}'); every value in them is meant to be fictional. One run each: the attacker samples." if SCENE_SET else "The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples."), "",
        "| Metric | Result |", "|---|---|",
        f"| Planted secrets removed | {pct(verified - sum(len(r['survived']) for r in ok), verified)} |",
        f"| Scenes with every secret removed | {pct(sum(not r['survived'] for r in with_secrets), len(with_secrets))} |",
        f"| Share of the frame changed (mean) | {100 * mean([r['changed'] for r in ok]):.1f}% |",
        f"| Leak scenes flagged (worst exposure specific or exact) | {pct(sum(worst(r['exposure_before']) > 2 for r in leaky), len(leaky))} |",
        f"| Control scenes falsely flagged | {pct(sum(worst(r['exposure_before']) > 2 for r in controls), len(controls))} |",
        f"| Text check found the expected kinds | {pct(hit, len(expecting))} |",
        f"| Values echoed in the attacker's report | {pct(sum(len(r['values_printed']) for r in ok), printable)} |",
        f"| Mean seconds per scene | {mean([r['seconds'] for r in ok]):.0f} |",
        "", "| Scene | Secrets removed | Changed | Text check found | Edits |", "|---|---|---|---|---|",
    ]
    for r in recs:
        if "error" in r:
            lines.append(f"| {r['id']} | error: {r['error']} | | | |")
            continue
        gone = len(r["verified"]) - len(r["survived"])
        lines.append(f"| {r['id']} | {gone}/{len(r['verified'])} | {100 * r['changed']:.1f}% | "
                     f"{', '.join(r['textcheck_found']) or '-'} | {len(r['edits'])} |")
    return "\n".join(lines) + "\n"


def requests_section(reused: int) -> str:
    """The requests this invocation sent, as counted by bench/requestcount.py. Scenes reused from an earlier run sent none now."""
    note = (f"{reused} scene(s) were reused from earlier runs and sent no requests now; their requests were not counted. "
            if reused else "")
    return ("\n## API requests sent by this invocation (counted)\n\n" + note +
            "Every request that actually went out, retries included. Provider quota is per model, so read the by-model rows.\n\n"
            + "\n".join(COUNTER.lines()) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None, help="results folder name; defaults to the REGION setting")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--all", action="store_true", help="run all ten scenes, not just the five core ones")
    ap.add_argument("--verifier", default="", help="model that reads the before and after photos (default: the attacker's model)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--set", default="", help="another scene set under bench/india/<set> (images and scenes.json); give it its own --tag")
    args = ap.parse_args()
    if meta.open_client is None:
        raise SystemExit("Set OPEN_API_KEY (and the Gemma 4 values) in .env first")
    COUNTER.install(meta.open_client)
    from app import regions
    tag = args.tag or ("-".join(p.NAME.split()[0].lower() for p in regions.active()) or "global")
    if args.set and not args.tag:
        raise SystemExit("--set needs its own --tag, so the published results are not overwritten")
    out = ROOT / "results" / tag
    (out / "scenes").mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    base = ROOT / args.set if args.set else ROOT
    global IMAGES
    IMAGES = base if args.set else IMAGES
    scenes = json.loads((base / "scenes.json").read_text(encoding="utf-8"))
    global VERIFIER, SCENE_SET
    VERIFIER = args.verifier
    SCENE_SET = args.set
    if not args.all and not args.only:
        scenes = [sc for sc in scenes if sc.get("core", True)]
    if args.only:
        scenes = [s for s in scenes if s["id"] in args.only.split(",")]
    with ThreadPoolExecutor(args.workers) as pool:
        recs = list(pool.map(lambda s: run_scene(s, out, args.force), scenes))
    summary = summarize(recs, tag)
    reused = sum("error" not in r and "requests" not in r for r in recs)
    if COUNTER.total():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        summary += requests_section(reused)
        (out / f"requests-{stamp}.json").write_text(json.dumps(
            {"snapshot": COUNTER.snapshot(), "rows": [list(k) + [n] for k, n in sorted(COUNTER.rows.items()) if n]},
            indent=1), encoding="utf-8")
        print("\n".join(COUNTER.lines()))
    (out / "summary.md").write_text(summary, encoding="utf-8")
    print(f"wrote {out / 'summary.md'}")


if __name__ == "__main__":
    main()
