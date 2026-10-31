"""Offline benchmark of the deterministic text detector (meta.text_check): no API key, no network, no randomness.

It scores the regular expressions and the Verhoeff checksum that run beside the model, on hand-written, made-up texts
(bench/india/detector_cases.json). It does NOT score the model or the image edits: those are in bench.indiabench.

Scoring is per case and per kind of detail: a kind is a true positive when the case contains it and the detector found
it, a false positive when the detector found a kind the case does not contain, and a false negative when the case
contains a kind the detector missed. Counts of matches inside one case are ignored, because "Door No. 12, Gandhi Nagar"
is one address to a reader and two matches to a pattern. The prompt-injection detector is scored as a yes/no per case.

Usage: uv run python -m bench.detectorbench [--tag NAME]
       REGION=global uv run python -m bench.detectorbench      (India pack off; PowerShell: $env:REGION='global')
Writes bench/india/results/detector/<tag>.json and <tag>.md, where tag defaults to the active region packs. Existing files
under bench/india/results/in, global and the *-gemma4 folders are never touched.
"""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

from app import meta, regions

HERE = Path(__file__).parent / "india"
CASES = HERE / "detector_cases.json"
OUT = HERE / "results" / "detector"
CRLF, LF = bytes([13, 10]), bytes([10])
REPEATS = 200  # passes over the whole set, only to time it: one pass is a few milliseconds


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None  # 0 when it found nothing it should have
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f}


def show(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def evaluate(spec: dict) -> dict:
    cases, injection = spec["cases"], spec["injection"]
    found = {c["id"]: set(meta.text_check(c["texts"])["found"]) for c in cases}
    kinds = sorted({k for c in cases for k in c["expect"]} | set(meta.CONTACT))
    per_kind = {k: [0, 0, 0] for k in kinds}
    per_group: dict[str, list[int]] = {}
    misses, extras = [], []
    for c in cases:
        want, got = set(c["expect"]), found[c["id"]]
        g = per_group.setdefault(c["group"], [0, 0, 0])
        for k in kinds:
            idx = 0 if k in want and k in got else 1 if k in got else 2 if k in want else None
            if idx is None:
                continue
            per_kind[k][idx] += 1
            g[idx] += 1
        misses += [(c["id"], k) for k in sorted(want - got)]
        extras += [(c["id"], k) for k in sorted(got - want)]
    inj = [0, 0, 0, 0]  # tp, fp, fn, tn
    inj_wrong = []
    for c in injection:
        said = meta.text_check(c["texts"])["injection"]
        inj[0 if said and c["expect"] else 1 if said else 2 if c["expect"] else 3] += 1
        if said != c["expect"]:
            inj_wrong.append((c["id"], "missed" if c["expect"] else "false alarm"))
    tp, fp, fn = (sum(v[i] for v in per_kind.values()) for i in range(3))
    return {
        "overall": prf(tp, fp, fn),
        "macro_f1": sum(m["f1"] for m in (prf(*v) for v in per_kind.values()) if m["f1"] is not None) /
                    max(1, sum(prf(*v)["f1"] is not None for v in per_kind.values())),
        "per_kind": {k: prf(*v) for k, v in per_kind.items() if any(v)},
        "per_group": {g: prf(*v) for g, v in per_group.items()},
        "misses": misses, "false_alarms": extras,
        "injection": {**prf(inj[0], inj[1], inj[2]), "tn": inj[3], "cases": len(injection), "wrong": inj_wrong},
        "cases": len(cases), "cases_with_nothing": sum(not c["expect"] for c in cases),
        "expected_items": sum(len(c["expect"]) for c in cases),
    }


def time_it(spec: dict) -> dict:
    texts = [c["texts"] for c in spec["cases"]] + [c["texts"] for c in spec["injection"]]
    t = time.perf_counter()
    for _ in range(REPEATS):
        for tx in texts:
            meta.text_check(tx)
    total = time.perf_counter() - t
    return {"texts": len(texts), "repeats": REPEATS, "seconds_per_text_ms": round(1000 * total / (REPEATS * len(texts)), 4),
            "seconds_per_full_pass_ms": round(1000 * total / REPEATS, 3)}


def markdown(tag: str, spec: dict, res: dict, timing: dict, wall: float, digest: str) -> str:
    o = res["overall"]
    lines = [
        f"# Text detector benchmark (offline, REGION={tag})", "",
        "Measured, deterministic, no API calls. This scores the regular expressions and the Aadhaar checksum, not the model "
        "and not the photo edits. The texts are hand-written and made up, so the numbers show how the patterns do on the "
        "formats we thought of, not on all real photos.", "",
        f"- Test texts: {res['cases']} detail cases ({res['cases_with_nothing']} with nothing private in them) and "
        f"{res['injection']['cases']} prompt-injection cases. Items that should be found: {res['expected_items']}.",
        f"- Dataset: `bench/india/detector_cases.json`, sha256 `{digest[:16]}`. Python {platform.python_version()}, {platform.system()}.",
        f"- Total benchmark time: {wall * 1000:.0f} ms for the whole run (loading, scoring, and {REPEATS} timing passes). "
        f"One detector pass over every text: {timing['seconds_per_full_pass_ms']} ms, about {timing['seconds_per_text_ms']} ms per text. "
        "Timings depend on the machine.", "",
        "## Overall (per case and kind, micro-averaged)", "",
        "| TP | FP | FN | Precision | Recall | F1 | Macro F1 over kinds |", "|---|---|---|---|---|---|---|",
        f"| {o['tp']} | {o['fp']} | {o['fn']} | {show(o['precision'])} | {show(o['recall'])} | {show(o['f1'])} | {show(res['macro_f1'])} |", "",
        "## By kind", "", "| Kind | TP | FP | FN | Precision | Recall | F1 |", "|---|---|---|---|---|---|---|",
    ]
    for k, m in res["per_kind"].items():
        lines.append(f"| {k} | {m['tp']} | {m['fp']} | {m['fn']} | {show(m['precision'])} | {show(m['recall'])} | {show(m['f1'])} |")
    lines += ["", "n/a means the metric has no denominator (nothing expected, or nothing found).", "",
              "## By kind of test text", "",
              "`positive` are ordinary formats, `hard_negative` are look-alikes that are not private, `known_limit` are real formats "
              "the patterns are not built for, `scene_like` mimic the benchmark scenes.", "",
              "| Group | TP | FP | FN | Precision | Recall |", "|---|---|---|---|---|---|"]
    for g, m in res["per_group"].items():
        lines.append(f"| {g} | {m['tp']} | {m['fp']} | {m['fn']} | {show(m['precision'])} | {show(m['recall'])} |")
    i = res["injection"]
    lines += ["", "## Prompt-injection note detector (yes or no per text)", "",
              "| TP | FP | FN | TN | Precision | Recall | F1 |", "|---|---|---|---|---|---|---|",
              f"| {i['tp']} | {i['fp']} | {i['fn']} | {i['tn']} | {show(i['precision'])} | {show(i['recall'])} | {show(i['f1'])} |", "",
              "## Misses and false alarms (case, kind)", "",
              "Missed: " + (", ".join(f"{c}: {k}" for c, k in res["misses"]) or "none"), "",
              "False alarms: " + (", ".join(f"{c}: {k}" for c, k in res["false_alarms"]) or "none"), "",
              "Injection mistakes: " + (", ".join(f"{c} ({w})" for c, w in i["wrong"]) or "none"), "",
              "## Not measured here", "",
              "Precision, recall and F1 for the image-level result (did the model find and the edit remove a clue in a photo) are "
              "not calculated: a photo has no agreed list of every clue in it, so false positives and false negatives would be "
              "guesses. The image benchmark reports secrets removed, control false alarms and share of the frame changed instead "
              "(`docs/benchmark.md`).", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    t0 = time.perf_counter()
    raw = CASES.read_bytes()
    spec = json.loads(raw.decode("utf-8"))
    tag = args.tag or ("-".join(p.NAME.split()[0].lower() for p in regions.active()) or "global")
    res = evaluate(spec)
    timing = time_it(spec)
    wall = time.perf_counter() - t0
    OUT.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(raw.replace(CRLF, LF)).hexdigest()  # the same on Windows and Linux checkouts
    (OUT / f"{tag}.json").write_text(json.dumps({"region": tag, "dataset_sha256": digest, "timing": timing,
                                                 "wall_seconds": round(wall, 4), **res},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    md = markdown(tag, spec, res, timing, wall, digest)
    (OUT / f"{tag}.md").write_text(md, encoding="utf-8")
    print(md.encode("ascii", "replace").decode())
    print(f"wrote {OUT / (tag + '.md')}")


if __name__ == "__main__":
    main()
