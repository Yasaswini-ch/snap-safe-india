"""Draw the Snap Safe India logo: a viewfinder around a saffron-white-green shield with a check mark, on indigo.
Writes static/favicon.png (32), apple-touch-icon.png (180), icon-192.png and icon-512.png. Everything sits inside the
central 80% of the square so the 512 icon also works as a maskable icon.

Usage: uv run python scripts/make_logo.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

STATIC = Path(__file__).parent.parent / "static"
BIG = 2048
INDIGO, PAPER, SAFFRON, WHITE, GREEN, INK = (38, 33, 92), (245, 239, 230), (232, 115, 12), (252, 250, 245), (19, 136, 8), (27, 26, 46)


def bezier(p0, p1, p2, n=40):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def logo() -> Image.Image:
    s = BIG
    px = lambda pts: [(x * s, y * s) for x, y in pts]  # noqa: E731
    img = Image.new("RGB", (s, s), INDIGO)
    d = ImageDraw.Draw(img)
    # viewfinder corners
    w, a, b = 0.045, 0.22, 0.38  # stroke, outer and inner reach from the edge of the 0.22-0.78 frame
    for sx in (0, 1):
        for sy in (0, 1):
            x0, y0 = (0.22, 0.22) if not sx else (0.78, 0.22)
            x0 = 0.22 if sx == 0 else 0.78
            y0 = 0.22 if sy == 0 else 0.78
            dx, dy = (1 if sx == 0 else -1), (1 if sy == 0 else -1)
            d.rectangle(sorted_box(x0, y0, x0 + dx * 0.17, y0 + dy * w, s), fill=PAPER)
            d.rectangle(sorted_box(x0, y0, x0 + dx * w, y0 + dy * 0.17, s), fill=PAPER)
    # shield
    left, right, top, mid, tip = 0.35, 0.65, 0.31, 0.52, 0.71
    outline = ([(left, top), (right, top), (right, mid)] + bezier((right, mid), (right, 0.64), (0.5, tip))
               + bezier((0.5, tip), (left, 0.64), (left, mid)))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).polygon(px(outline), fill=255)
    bands = Image.new("RGB", (s, s), WHITE)
    bd = ImageDraw.Draw(bands)
    bd.rectangle([0, 0, s, 0.445 * s], fill=SAFFRON)
    bd.rectangle([0, 0.575 * s, s, s], fill=GREEN)
    img.paste(bands, (0, 0), mask)
    # check mark over the bands
    d = ImageDraw.Draw(img)
    check = px([(0.435, 0.505), (0.488, 0.558), (0.575, 0.435)])
    d.line(check, fill=INK, width=int(0.036 * s), joint="curve")
    for x, y in (check[0], check[2]):
        r = 0.018 * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=INK)
    return img


def sorted_box(x0, y0, x1, y1, s):
    return [min(x0, x1) * s, min(y0, y1) * s, max(x0, x1) * s, max(y0, y1) * s]


def main():
    big = logo()
    for name, size in (("icon-512", 512), ("icon-192", 192), ("apple-touch-icon", 180)):
        big.resize((size, size), Image.LANCZOS).save(STATIC / f"{name}.png")
        print(f"wrote static/{name}.png")
    # At 32 px the viewfinder crowds the shield, so the favicon is a tight crop of the shield alone
    c = int(0.265 * BIG), int(0.255 * BIG)
    side = int(0.47 * BIG)
    big.crop((c[0], c[1], c[0] + side, c[1] + side)).resize((32, 32), Image.LANCZOS).save(STATIC / "favicon.png")
    print("wrote static/favicon.png")


if __name__ == "__main__":
    main()
