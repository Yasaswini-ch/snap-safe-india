"""Indian benchmark: rendered scenes with planted fictional secrets, scored by whether those secrets are still legible.

Ground truth is the planted strings. A verifier pass transcribes every readable text in
the original and in the cleaned photo; a secret counts only if it was legible in the original. The agent runs in
private mode, so the attacker is whatever OPEN_MODEL is (Gemma 4 in this fork). Regions come from REGION, so running
once with REGION=in and once with REGION=global shows what the India pack adds.

Usage: REGION=in uv run --env-file .env python -m bench.indiabench [--tag in] [--workers 3] [--only id,id] [--force]
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


def evaluate(scene: dict, out: Path) -> dict:
    img, _ = pipeline.load_image((IMAGES / f"{scene['id']}.jpg").read_bytes())
    secrets = with_parts(scene["secrets"])
    rec = {"id": scene["id"], "kind": scene["kind"], "secrets": secrets, "expect": scene["expect"]}
    rec["verified"] = legible(secrets, meta.read_text(img, private=True))
    t = time.time()
    events = list(agent.run([img], attack=functools.partial(meta.attack, private=True), private=True,
                            read=functools.partial(meta.read_text, private=True)))
    rec["seconds"] = round(time.time() - t, 1)
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
    rec["survived"] = legible(rec["verified"], meta.read_text(ours, private=True))
    rec["changed"] = round(changed(img, ours), 4)
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
        "The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.", "",
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None, help="results folder name; defaults to the REGION setting")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if meta.open_client is None:
        raise SystemExit("Set OPEN_API_KEY (and the Gemma 4 values) in .env first")
    from app import regions
    tag = args.tag or ("-".join(p.NAME.split()[0].lower() for p in regions.active()) or "global")
    out = ROOT / "results" / tag
    (out / "scenes").mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    scenes = json.loads((ROOT / "scenes.json").read_text(encoding="utf-8"))
    if args.only:
        scenes = [s for s in scenes if s["id"] in args.only.split(",")]
    with ThreadPoolExecutor(args.workers) as pool:
        recs = list(pool.map(lambda s: run_scene(s, out, args.force), scenes))
    (out / "summary.md").write_text(summarize(recs, tag), encoding="utf-8")
    print(f"wrote {out / 'summary.md'}")


if __name__ == "__main__":
    main()
