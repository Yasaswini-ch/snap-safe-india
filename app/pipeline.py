"""Pixel side of the pipeline: masks, edits and mask-bounded compositing. No model calls here."""
import base64
import io

import cv2
import numpy as np
from PIL import Image, ImageOps

ACTIONS = ("erase", "pixelate", "blur", "keep")
# A small file can declare a huge canvas (a decompression bomb). JPEG decodes straight to a reduced size via draft(),
# so it may be big; anything else is decoded in full and must be small enough for a 512 MB host.
MAX_PIXELS = {"JPEG": 100_000_000, "MPO": 100_000_000, "PNG": 25_000_000, "WEBP": 25_000_000}


def load_image(data: bytes, max_side: int | None = None) -> tuple[np.ndarray, dict]:
    """Decode upload to an upright RGB array and report what the file's metadata leaks."""
    img = Image.open(io.BytesIO(data))
    if img.width * img.height > MAX_PIXELS.get(img.format, 0):
        raise ValueError(f"{img.format} {img.width}x{img.height} is not an accepted photo")
    if max_side:
        img.draft("RGB", (max_side, max_side))
    exif = img.getexif()
    device = " ".join(str(v).strip() for v in (exif.get(0x010F), exif.get(0x0110)) if v)
    metadata = {"gps": bool(exif.get_ifd(0x8825)), "device": device or None}
    # Phone photos are stored sideways with an orientation tag; boxes are relative to the upright image.
    img = ImageOps.exif_transpose(img).convert("RGB")
    if max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)
    return np.asarray(img).copy(), metadata


def encode_png(img: np.ndarray) -> bytes:
    """Lossless and metadata-free, so untouched pixels stay byte-identical and EXIF/GPS never leaves."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, "PNG")
    return buf.getvalue()


def encode_jpeg_b64(img: np.ndarray, quality: int = 82) -> str:
    """Small progress frames for the UI. The downloadable result stays the lossless PNG."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, "JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode()


def box_mask(shape, box) -> np.ndarray:
    """Normalized [x0, y0, x1, y1] -> boolean mask. Fallback when segmentation gives nothing."""
    h, w = shape[:2]
    x0, y0, x1, y1 = box
    mask = np.zeros((h, w), bool)
    mask[int(y0 * h):int(np.ceil(y1 * h)), int(x0 * w):int(np.ceil(x1 * w))] = True
    return mask


def snap_box(img: np.ndarray, box, core=None) -> list[float]:
    """Shrink a loose box to the ink inside it. `box` is the search window (normalized [x0, y0, x1, y1]); `core` is the
    model's own box, which may be smaller when the window was widened. Ink is whatever differs from its local
    background (text, a barcode, a plate's characters); letters on one line are merged, and the pieces that touch the
    core are kept. Pieces that run edge to edge through the window (a card's border) are ignored. With no usable ink the
    box comes back unchanged, so a snap can only tighten an edit, never lose one."""
    h, w = img.shape[:2]
    core = core or box
    x0, y0, x1, y1 = (int(round(box[0] * w)), int(round(box[1] * h)), int(round(box[2] * w)), int(round(box[3] * h)))
    cx0, cy0, cx1, cy1 = (int(round(core[0] * w)), int(round(core[1] * h)), int(round(core[2] * w)), int(round(core[3] * h)))
    if x1 - x0 < 8 or y1 - y0 < 8:
        return list(box)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)[y0:y1, x0:x1]
    k = max(15, (min(gray.shape) // 2) | 1)
    ink = (np.abs(gray.astype(np.int16) - cv2.blur(gray, (k, k)).astype(np.int16)) > 26).astype(np.uint8)
    if ink.sum() < 12:
        return list(box)
    line = max(7, int(0.6 * max(cy1 - cy0, 1)))  # letters of one line merge; separate lines stay apart
    merged = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_RECT, (line, 3)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(merged)
    keep, nearest = [], None
    hh, ww = gray.shape
    for i in range(1, n):
        x, y, cw, ch, _ = stats[i]
        spans_x, spans_y = x <= 1 and x + cw >= ww - 1, y <= 1 and y + ch >= hh - 1
        if (spans_x and ch < 0.25 * hh) or (spans_y and cw < 0.25 * ww):
            continue  # a border or an edge running through the window
        gx0, gy0, gx1, gy1 = x + x0, y + y0, x + cw + x0, y + ch + y0
        if gx1 > cx0 and gx0 < cx1 and gy1 > cy0 and gy0 < cy1:
            keep.append(i)
        else:
            d = (((gx0 + gx1) - (cx0 + cx1)) / 2) ** 2 + (((gy0 + gy1) - (cy0 + cy1)) / 2) ** 2
            if nearest is None or d < nearest[0]:
                nearest = (d, i)
    if not keep and nearest is not None:
        keep = [nearest[1]]  # the model's box missed: take the closest ink instead
    if not keep:
        return list(box)
    ys, xs = np.nonzero(ink & np.isin(labels, keep).astype(np.uint8))
    if len(xs) < 8:
        return list(box)
    pad = max(3, int(0.3 * (ys.max() - ys.min() + 1)))
    sx0, sy0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    sx1, sy1 = min(ww, xs.max() + 1 + pad), min(hh, ys.max() + 1 + pad)
    return [(x0 + sx0) / w, (y0 + sy0) / h, (x0 + sx1) / w, (y0 + sy1) / h]


def grow(mask: np.ndarray, px: int) -> np.ndarray:
    """Pad the mask so edits cover anti-aliased edges the box or segment missed."""
    k = 2 * px + 1
    return cv2.dilate(mask.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)


def composite(orig: np.ndarray, edited: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Take edited pixels only inside the mask. Everything outside is the original, guaranteed."""
    return np.where(mask[..., None], edited, orig)


def blur(img: np.ndarray) -> np.ndarray:
    k = max(img.shape[:2]) // 25 | 1
    return cv2.GaussianBlur(img, (k, k), 0)


def pixelate(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    block = max(8, max(h, w) // 60)
    small = cv2.resize(img, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def inpaint(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Classic fill. Fine for small text and barcodes; large objects need the generative edit."""
    return cv2.inpaint(img, mask.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)


if __name__ == "__main__":
    # Self-check for the core promise: edits never touch pixels outside their mask.
    rng = np.random.default_rng(0)
    orig = rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)
    mask = grow(box_mask(orig.shape, (0.3, 0.3, 0.6, 0.5)), 3)
    for name, edited in [("blur", blur(orig)), ("pixelate", pixelate(orig)), ("inpaint", inpaint(orig, mask))]:
        out = composite(orig, edited, mask)
        assert np.array_equal(out[~mask], orig[~mask]), f"{name} changed pixels outside the mask"
        assert not np.array_equal(out[mask], orig[mask]), f"{name} left the masked area untouched"
    back, meta = load_image(encode_png(out))
    assert np.array_equal(back, out) and meta == {"gps": False, "device": None}
    # A 9000x9000 PNG is a few hundred KB on disk and 243 MB decoded: refused before decoding.
    bomb = io.BytesIO()
    Image.new("1", (9000, 9000)).save(bomb, "PNG")
    try:
        load_image(bomb.getvalue(), 2048)
        raise AssertionError("decompression bomb was decoded")
    except ValueError:
        pass
    print("pipeline ok")
