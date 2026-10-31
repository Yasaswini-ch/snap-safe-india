"""Copy the realistic-photo results into static/india/real for the page's results section.

Usage: uv run python bench/india/real/publish.py   (after bench/india/real/run.py has run)
Photos are shrunk to 900 px wide so the page stays light.
"""
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
OUT = HERE.parent.parent.parent / "static" / "india" / "real"
LABELS = {"parcel_real": "Parcel on a doorstep", "upi_real": "Payment screen at a counter", "plate_real": "Number plate at a gate"}


def shrink(src: Path, dst: Path):
    img = Image.open(src).convert("RGB")
    img.thumbnail((900, 900))
    img.save(dst, quality=85)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for path in sorted((HERE / "results" / "scenes").glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if "error" in r:
            continue
        shrink(HERE / f"{r['id']}.jpg", OUT / f"{r['id']}.jpg")
        shrink(HERE / "results" / "images" / f"{r['id']}_after.jpg", OUT / f"{r['id']}_after.jpg")
        items.append({"id": r["id"], "label": LABELS.get(r["id"], r["id"]), "secrets": len(r["verified"]),
                      "removed": len(r["verified"]) - len(r["survived"]), "changed": round(100 * r["changed"], 1),
                      "seconds": r["seconds"]})
    model = json.loads(next((HERE / "results" / "scenes").glob("*.json")).read_text(encoding="utf-8")).get("model", "")
    (OUT / "results.json").write_text(json.dumps({"model": model, "items": items}, indent=1), encoding="utf-8")
    print(f"{len(items)} photos written to {OUT}")


if __name__ == "__main__":
    main()
