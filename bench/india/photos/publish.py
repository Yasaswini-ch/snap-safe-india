"""Copy the photograph-like set's results into static/india/photos for the page's "Photo-style images" section.

Usage: uv run python bench/india/photos/publish.py   (after bench.indiabench --set photos --tag photos-in has run)
Photos are shrunk to 900 px so the page stays light. Nothing here calls a model.
"""
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
RESULTS = HERE.parent / "results" / "photos-in"
OUT = HERE.parent.parent.parent / "static" / "india" / "photos"
LABELS = {
    "photo_tea_menu": "Tea stall menu (nothing to hide)",
    "photo_medical_sign": "Telugu and English shop sign",
    "photo_library_card": "Library member card",
    "photo_house_board": "House gate with name and PIN plates",
    "photo_upi_kirana": "Hindi UPI shop stand",
    "photo_hindi_parcel": "Hindi parcel label",
    "photo_telugu_house": "Telugu house plate",
}


def shrink(src: Path, dst: Path):
    img = Image.open(src).convert("RGB")
    img.thumbnail((900, 900))
    img.save(dst, quality=85)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for sid in LABELS:
        r = json.loads((RESULTS / "scenes" / f"{sid}.json").read_text(encoding="utf-8"))
        shrink(HERE / f"{sid}.jpg", OUT / f"{sid}.jpg")
        shrink(RESULTS / "images" / f"{sid}_after.jpg", OUT / f"{sid}_after.jpg")
        items.append({"id": sid, "label": LABELS[sid], "secrets": len(r["verified"]),
                      "removed": len(r["verified"]) - len(r["survived"]), "changed": round(100 * r["changed"], 1),
                      # a leak scene whose agent stopped after one attack and is not marked safe never finished its re-check
                      "complete": not (r["attacks"] == 1 and not r["safe"]), "safe": r["safe"], "attacks": r["attacks"]})
    model = json.loads((RESULTS / "scenes" / "photo_tea_menu.json").read_text(encoding="utf-8")).get("model", "")
    (OUT / "results.json").write_text(json.dumps({"model": model, "items": items}, indent=1), encoding="utf-8")
    print(f"{len(items)} photos written to {OUT}")


if __name__ == "__main__":
    main()
