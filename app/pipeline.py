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


def _ring(mask: np.ndarray, px: int) -> np.ndarray:
    k = 2 * px + 1
    return cv2.dilate(mask.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool) & ~mask


def _ring_width(mask: np.ndarray) -> int:
    ys, xs = np.nonzero(mask)
    return max(3, min(12, int(max(np.ptp(ys), np.ptp(xs)) * 0.08)))


def plain_around(img: np.ndarray, mask: np.ndarray, near: int = 40, share: float = 0.8) -> bool:
    """True when most of the pixels just outside the mask are close to one colour, so a flat fill will not show as a
    patch. A little other text beside it (the next line of a label) is allowed; a different object is not."""
    ring = _ring(mask, _ring_width(mask))
    if ring.sum() < 20:
        return False
    px = img[ring].astype(int)
    return float((np.abs(px - np.median(px, axis=0)).max(-1) <= near).mean()) >= share


# What a covered value is replaced with when it is number-like: obviously a placeholder, never a believable value, and
# never something the text check would take for a real one (a plate needs digits in the right places, so this has none).
PLACEHOLDERS = [(("plate", "registration"), "XX XX XX XXXX"), (("phone", "mobile", "cell"), "00000 00000"),
                (("pin code", "postal", "zip"), "000000"), (("upi",), "XXXX@XXXX"),
                (("aadhaar", "id number", "member", "roll", "account", "reference", "pan ", "card number", "ticket", "pnr",
                  "booking", "awb", "tracking", "number"), "XXXX XXXX 0000")]


def placeholder_for(label: str) -> str:
    label = f"{label.lower()} "
    return next((text for words, text in PLACEHOLDERS if any(w in label for w in words)), "")


def clean_fill(img: np.ndarray, mask: np.ndarray, placeholder: str = "") -> np.ndarray:
    """Cover the mask with the colour around it, softened so a gradient (glare, shadow) carries across, and, for a
    number-like value, a grey placeholder in its place. Only pixels inside the mask differ from the input."""
    bg = np.median(img[_ring(mask, _ring_width(mask))], axis=0)
    filled = img.copy()
    filled[mask] = bg
    k = max(img.shape[:2]) // 40 | 1
    out = np.where(mask[..., None], cv2.GaussianBlur(filled, (k, k), 0), img)
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    if placeholder and (x1 - x0) >= 24 and (y1 - y0) >= 8:
        from PIL import ImageDraw, ImageFont
        pil = Image.fromarray(out.astype(np.uint8))
        draw = ImageDraw.Draw(pil)
        size = max(6, int((y1 - y0) * 0.6))
        font = ImageFont.load_default(size)
        while draw.textlength(placeholder, font=font) > (x1 - x0) * 0.9 and size > 6:
            size -= 1
            font = ImageFont.load_default(size)
        w = draw.textlength(placeholder, font=font)
        layer = Image.new("L", pil.size, 0)
        ImageDraw.Draw(layer).text((x0 + ((x1 - x0) - w) / 2, y0 + ((y1 - y0) - size) / 2), placeholder, font=font, fill=255)
        ink = tuple(int(v) for v in bg * 0.6)
        drawn = np.asarray(layer) > 0
        out = np.where((drawn & mask)[..., None], np.array(ink, np.uint8), out)
    return out.astype(np.uint8)


if __name__ == "__main__":
    # Self-check for the core promise: edits never touch pixels outside their mask.
    rng = np.random.default_rng(0)
    orig = rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)
    mask = grow(box_mask(orig.shape, (0.3, 0.3, 0.6, 0.5)), 3)
    for name, edited in [("blur", blur(orig)), ("pixelate", pixelate(orig)), ("inpaint", inpaint(orig, mask))]:
        out = composite(orig, edited, mask)
        assert np.array_equal(out[~mask], orig[~mask]), f"{name} changed pixels outside the mask"
        assert not np.array_equal(out[mask], orig[mask]), f"{name} left the masked area untouched"
    # A clean fill matches the plain colour around it, never touches pixels outside the mask, and only draws a
    # placeholder for number-like values; a busy background is not "plain".
    flat = np.full((200, 300, 3), (205, 208, 214), np.uint8)
    flat[80:110, 60:240] = (30, 30, 36)  # dark "text" on a pale plate
    hole = grow(box_mask(flat.shape, (60 / 300, 80 / 200, 240 / 300, 110 / 200)), 2)
    assert plain_around(flat, hole) and not plain_around(orig, mask)
    tidy = composite(flat, clean_fill(flat, hole), hole)
    assert np.array_equal(tidy[~hole], flat[~hole]) and np.abs(tidy[hole].astype(int) - 205).max() < 20
    marked = composite(flat, clean_fill(flat, hole, "XXXX XXXX 0000"), hole)
    assert (marked[hole].astype(int).sum(-1) < 400).any() and np.array_equal(marked[~hole], flat[~hole])
    assert placeholder_for("vehicle number plate") == "XX XX XX XXXX" and placeholder_for("phone number") == "00000 00000"
    assert placeholder_for("aadhaar number") == "XXXX XXXX 0000" and placeholder_for("house name board") == ""
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
