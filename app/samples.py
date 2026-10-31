"""Recorded agent runs for the sample gallery: real results that play instantly and cost no API calls.

Record (needs OPEN_API_KEY): uv run --env-file .env python -m app.samples [name ...]
"""
import asyncio
import base64
import functools
import json
import shutil
import time
from pathlib import Path

SAMPLES = Path(__file__).parent.parent / "static" / "samples"
INDIA = Path(__file__).parent.parent / "bench" / "india" / "images"  # the Indian benchmark scenes (bench/india)
REAL = INDIA.parent / "real"  # the photo-style test images (bench/india/real)
PHOTOS = INDIA.parent / "photos"  # the team's photograph-like images (bench/india/photos)
# sample name -> benchmark photos, served as static/samples/{name}-{1..n}.jpg. Several photos = one account scan.
SOURCES = {"in_id_card": ["id_card"], "in_parcel": ["parcel_label"], "in_plate": ["car_plate_in"],
           "in_upi": ["upi_screen"], "in_telugu": ["telugu_sign"],
           "in_tea": ["ctrl_tea_menu"],  # the control: nothing personal, so nothing should be edited
           "in_parcel_real": ["parcel_real"], "in_upi_real": ["upi_real"], "in_plate_real": ["plate_real"],  # photo-style images
           "in_photo_tea": ["photo_tea_menu"], "in_photo_sign": ["photo_medical_sign"], "in_photo_card": ["photo_library_card"],
           "in_photo_gate": ["photo_house_board"], "in_photo_upi_hi": ["photo_upi_kirana"],
           "in_photo_parcel_hi": ["photo_hindi_parcel"], "in_photo_house_te": ["photo_telugu_house"],
           "in_photo_store_ta": ["photo_tamil_store"], "in_photo_clinic_ta": ["photo_tamil_clinic"]}  # photograph-like images
PRIVATE = set(SOURCES)  # recorded through the open-model path (OPEN_MODEL), edits on the server
# What each post would say, for samples that have a caption. Captions often name what the photo's edits hide.
CAPTIONS: dict[str, str | list[str]] = {
    "in_parcel": "Ordered last week and it is finally here 📦 Siripuram delivery was quick! #unboxing",
    "in_plate": "Our new ride is finally home 🚗 #newcar #vizag",
    "in_plate_real": "Our new ride is finally home 🚗 #newcar #vizag",
}
SPEEDUP = 4


def recorded() -> list[str]:
    """Names of the samples that have a recording, for the page's gallery."""
    return sorted(p.name[:-len(".ndjson")] for p in SAMPLES.glob("*.ndjson")) if SAMPLES.exists() else []


def recorded_with(name: str) -> dict:
    """{model, host} a sample was recorded with; empty for recordings made before this was kept."""
    path = SAMPLES / f"{name}.model.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def captions(name: str) -> list[str]:
    """One per photo of the sample: a single string is the first photo's caption."""
    c = CAPTIONS.get(name, "")
    return list(c) if isinstance(c, list) else [c]


async def replay(name: str, first: str = "", speed: float = SPEEDUP):
    """Yield `first`, then the recorded NDJSON lines, paced like the real run but `speed` times faster.
    Async so a replay waits without holding one of the server's worker threads."""
    yield first
    prev = 0.0
    for line in (SAMPLES / f"{name}.ndjson").read_text(encoding="utf-8").splitlines():
        t = json.loads(line)["t"]
        await asyncio.sleep(min(max(t - prev, 0.0) / speed, 30.0 / speed))
        prev = t
        yield line + "\n"


def record(name: str) -> None:
    from . import agent, meta, pipeline

    SAMPLES.mkdir(parents=True, exist_ok=True)
    imgs = []
    for i, source in enumerate(SOURCES[name], 1):
        src = SAMPLES / f"{name}-{i}.jpg"
        if not src.exists():
            shutil.copy(next(p for p in (INDIA / f"{source}.jpg", REAL / f"{source}.jpg", PHOTOS / f"{source}.jpg") if p.exists()), src)
        imgs.append(pipeline.load_image(src.read_bytes())[0])
    t0, lines = time.time(), []
    private = name in PRIVATE
    events = agent.run(imgs, attack=functools.partial(meta.attack, private=private), private=private,
                       read=functools.partial(meta.read_text, private=private, effort=meta.ATTACK_EFFORT),
                       caption=captions(name), rewrite=functools.partial(meta.rewrite_caption, private=private))
    for event in events:
        event = {**event, "t": round(time.time() - t0, 1)}
        if event["type"] == "done":
            event["image_urls"] = []
            for i, png in enumerate(event.pop("images"), 1):
                (SAMPLES / f"{name}-{i}.safe.png").write_bytes(base64.b64decode(png))
                event["image_urls"].append(f"samples/{name}-{i}.safe.png")
        lines.append(json.dumps(event, ensure_ascii=False))
    (SAMPLES / f"{name}.ndjson").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Which model made this run, so a replay never takes the label of whatever model the server runs now
    (SAMPLES / f"{name}.model.json").write_text(json.dumps({"model": meta.OPEN_LABEL, "host": meta.OPEN_HOST}),
                                                encoding="utf-8")
    print(f"recorded {name}: {lines[-1][:160]}", flush=True)


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor

    from . import meta

    import sys

    names = sys.argv[1:] or list(SOURCES)
    assert meta.client or meta.open_client, "recording needs MODEL_API_KEY or OPEN_API_KEY (run with --env-file .env)"
    assert meta.open_client or not PRIVATE & set(names), "private samples need OPEN_API_KEY"
    assert meta.client or PRIVATE >= set(names), "non-private samples need MODEL_API_KEY"
    with ThreadPoolExecutor(len(names)) as pool:
        list(pool.map(record, names))
