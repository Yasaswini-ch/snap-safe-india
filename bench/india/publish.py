"""Copy the Indian benchmark's results and before/after images into static/india for the page's results section.

Usage: uv run python -m bench.india.publish [--all]   (after bench.indiabench has run for the tags below)
The page shows the five core scenes; --all shows every scene that has results.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "static" / "india"
TAGS = ("in", "global")
PRINTED_MIN = 6


def norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def totals(recs: list[dict]) -> dict:
    ok = [r for r in recs if "error" not in r]
    leaky = [r for r in ok if r["kind"] == "leak"]
    controls = [r for r in ok if r["kind"] == "control"]
    worst = lambda e: max(e.values(), default=0)  # noqa: E731
    with_secrets = [r for r in leaky if r["verified"]]
    expecting = [r for r in leaky if r["expect"]]
    printable = sum(len([s for s in r["verified"] if len(norm(s)) >= PRINTED_MIN]) for r in ok)
    return {
        "scenes": len(ok), "errors": len(recs) - len(ok),
        "secrets": sum(len(r["verified"]) for r in ok),
        "removed": sum(len(r["verified"]) - len(r["survived"]) for r in ok),
        "clean": sum(not r["survived"] for r in with_secrets), "with_secrets": len(with_secrets),
        "changed": round(100 * sum(r["changed"] for r in ok) / max(len(ok), 1), 1),
        "flagged": sum(worst(r["exposure_before"]) > 2 for r in leaky), "leak": len(leaky),
        "false_flags": sum(worst(r["exposure_before"]) > 2 for r in controls), "controls": len(controls),
        "text_hits": sum(set(r["expect"]) <= set(r["textcheck_found"]) for r in expecting), "expecting": len(expecting),
        "echoed": sum(len(r["values_printed"]) for r in ok), "printable": printable,
        "seconds": round(sum(r["seconds"] for r in ok) / max(len(ok), 1)),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runs, scenes = {}, {}
    spec = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
    shown = {sc["id"] for sc in spec if sc.get("core", True) or "--all" in sys.argv}
    for tag in TAGS:
        folder = HERE / "results" / tag
        recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((folder / "scenes").glob("*.json"))]
        recs = [r for r in recs if r["id"] in shown]
        if not recs:
            continue
        runs[tag] = totals(recs)
        for r in recs:
            scenes.setdefault(r["id"], {"id": r["id"], "kind": r["kind"]})[tag] = {
                "removed": len(r["verified"]) - len(r["survived"]), "secrets": len(r["verified"]),
                "changed": round(100 * r["changed"], 1), "found": r["textcheck_found"]}
        (OUT / tag).mkdir(exist_ok=True)
        for r in recs:
            after = folder / "images" / f"{r['id']}_after.jpg"
            if after.exists():
                shutil.copy(after, OUT / tag / after.name)
    for sid in scenes:
        shutil.copy(HERE / "images" / f"{sid}.jpg", OUT / f"{sid}.jpg")
    (OUT / "results.json").write_text(json.dumps({"runs": runs, "scenes": list(scenes.values())},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"published {len(scenes)} scenes, runs: {', '.join(runs) or 'none'} -> {OUT}")


if __name__ == "__main__":
    main()
