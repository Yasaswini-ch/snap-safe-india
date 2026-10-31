"""Draw the README banner and divider: the same pixel harbour as the page's hero, in a 240x96 grid scaled up 5x.

Usage: uv run python scripts/make_banner.py     (writes docs/img/banner.png and docs/img/divider.png)
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent.parent / "docs" / "img"
W, H, SCALE = 240, 96, 5

FONT = {  # 5x7 capitals, one string per row
    "A": "01110 10001 10001 11111 10001 10001 10001", "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110", "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000", "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001", "I": "01110 00100 00100 00100 00100 00100 01110",
    "N": "10001 11001 10101 10011 10001 10001 10001", "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "V": "10001 10001 10001 10001 10001 01010 00100", "Y": "10001 10001 01010 00100 00100 00100 00100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
}


def text(d, x, y, s, color, scale=1, shadow=None):
    for ch in s:
        for j, row in enumerate(FONT[ch].split()):
            for i, bit in enumerate(row):
                if bit == "1":
                    if shadow:
                        d.rectangle([x + i * scale + 1, y + j * scale + 1, x + (i + 1) * scale, y + (j + 1) * scale], fill=shadow)
                    d.rectangle([x + i * scale, y + j * scale, x + (i + 1) * scale - 1, y + (j + 1) * scale - 1], fill=color)
        x += 6 * scale


def width(s, scale):
    return len(s) * 6 * scale - scale


def scene(d, r):
    px = lambda x, y, c: d.point((round(x), round(y)), fill=c)  # noqa: E731
    rect = lambda x, y, w, h, c: d.rectangle([round(x), round(y), round(x + w) - 1, round(y + h) - 1], fill=c)  # noqa: E731
    sea, land = 76, 72

    def disc(cx, cy, rad, c, top=None):
        for j in range(-rad, rad + 1):
            for i in range(-rad, rad + 1):
                if i * i + j * j <= rad * rad and (top is None or cy + j < top):
                    px(cx + i, cy + j, c)

    sx, sy, sr = 74, 52, 6
    for j in range(-16, 17):
        for i in range(-16, 17):
            d2 = i * i + j * j
            if sr * sr < d2 <= sr * sr * 6.8 and (i + j) % 2 == 0 and sy + j < land - 4:
                px(sx + i, sy + j, "#e8efd9" if d2 < sr * sr * 3.4 else "#d9eadf")
    disc(sx, sy, sr, "#f7f1cf")

    def cloud(cx, cy, rad):
        discs = [(cx + (i - 3.5) * rad * 0.52, cy + (r.random() - 0.5) * rad * 0.5, round(rad * (0.55 + r.random() * 0.45))) for i in range(8)]
        for c, dy in (("#cfdcd3", 3), ("#e8eddf", 1.5), ("#f7f8ee", 0)):
            for x, y, dd in discs:
                disc(round(x), round(y + dy), dd, c, land - 8)

    cloud(120, 56, 11); cloud(40, 62, 8); cloud(205, 58, 9)
    for gx, gy in ((215, 46), (18, 52)):
        for i in range(3):
            px(gx - 3 - i, gy - i + 2, "#547570"); px(gx + 3 + i, gy - i + 2, "#547570")
        px(gx, gy + 2, "#547570")

    def hy(base, amp, f, ph, x):
        return base - amp * (0.5 + 0.5 * math.sin(x * f + ph) * math.cos(x * f * 0.37 + ph * 2))

    def hill(base, amp, f, ph, c, edge):
        for x in range(W):
            y = hy(base, amp, f, ph, x); rect(x, y, 1, sea - y, c); px(x, y, edge)

    hill(land - 20, 24, 0.035, 1.3, "#a9cbb9", "#c1ddcd")
    lx = 149; ly = round(hy(land - 20, 24, 0.035, 1.3, lx))
    rect(lx, ly - 11, 3, 11, "#f4f4ec"); rect(lx, ly - 8, 3, 2, "#cf5b50"); rect(lx, ly - 4, 3, 2, "#cf5b50")
    rect(lx - 1, ly - 13, 5, 2, "#47635f"); px(lx + 1, ly - 15, "#f2d36b")
    hill(land - 9, 14, 0.05, 4.1, "#8bb79f", "#a3cbb4")
    rect(0, sea, W, H - sea, "#8fbab6")
    for _ in range(W // 2):
        rect(r.random() * W, sea + 2 + r.random() * (H - sea - 3), 2 + r.random() * 4, 1, "#b2d3cf")
    for k in range(6):
        rect(sx - (6 - k) * 2, sea + 2 + k * 3, (6 - k) * 4 - 2, 1, "#e4efdc")
    rect(0, sea, W, 1, "#6f9d99")
    for bx in (96, 168):
        rect(bx - 3, sea + 2, 7, 1, "#b8574e"); rect(bx, sea - 3, 1, 5, "#5b4636"); rect(bx + 1, sea - 3, 2, 3, "#fbfaf2")
    bx, by = 120, sea + 8
    rect(bx - 7, by, 15, 3, "#c0554c"); rect(bx - 6, by + 3, 13, 1, "#8f3d37"); rect(bx - 8, by - 1, 2, 1, "#c0554c"); rect(bx + 7, by - 1, 2, 1, "#c0554c")
    rect(bx, by - 11, 1, 11, "#5b4636")
    for i in range(9):
        rect(bx + 1, by - 10 + i, max(1, 7 - int(i * 0.8)), 1, "#fbfaf2")
    for k in range(4):
        rect(bx - 6 + k, by + 5 + k * 2, 14 - k * 2, 1, "#6f9d99" if k % 2 else "#7aa8a5")

    def bank(x0, x1):
        rect(x0, land, x1 - x0, sea - land + 1, "#7fa974"); rect(x0, land, x1 - x0, 2, "#9cc58a")
        rect(x0, sea - 2, x1 - x0, 3, "#8c6a5e"); rect(x0, sea, x1 - x0, 1, "#6e514a")
        x = x0
        while x < x1:
            rect(x, land - 1 - r.randrange(2), 1, 2, "#6c9a63"); x += 2 + r.randrange(3)
        for _ in range(max(2, (x1 - x0) // 20)):
            fx = x0 + 3 + r.random() * (x1 - x0 - 6); c = "#e9806f" if r.random() < 0.5 else "#f1c46b"
            rect(fx, land - 3, 2, 2, c); rect(fx, land - 1, 1, 2, "#5f8a58")

    bank(0, 82); bank(158, W)

    def pine(x, h):
        top, body = land - h, h * 0.84
        rect(x, land - round(h * 0.18), 2, round(h * 0.18) + 1, "#7a5a4a")
        for y in range(int(body)):
            w = 1 + int((y / body) * h * 0.2 + (2 if y % 7 < 2 else 0)) + (1 if y > 6 and r.random() < 0.3 else 0)
            for i in range(-w, w + 1):
                edge = i in (-w, w) or y == 0
                c = "#46705a" if edge else (("#bcd8b0" if r.random() < 0.12 else "#a2c3a0") if i < -w * 0.25 else "#5f8d72" if i > w * 0.45 else "#7ea88a")
                px(x + 1 + i, top + y, c)
            if y % 7 == 2:
                for i in range(-w, w + 1):
                    px(x + 1 + i, top + y, "#4f7d62")

    def palm(x, h, lean):
        tx = x
        for y in range(h):
            tx = x + lean * (y / h) ** 1.6 * h * 0.3
            rect(tx, land - y, 2, 1, "#8a6a52" if y % 4 < 2 else "#725440")
        ty, cx = land - h, tx + 1
        for k in range(7):
            a = -math.pi * (0.05 + k / 6 * 0.9); ln = h * 0.42 + (k % 2) * 2
            for t in range(int(ln) + 1):
                fx, fy = cx + math.cos(a) * t, ty + math.sin(a) * t * 0.55 + (t * t) / (ln * 2.1)
                px(fx, fy, "#4f8a5b" if k % 2 else "#3f7650"); px(fx, fy + 1, "#6aa66d")
        rect(cx - 1, ty + 1, 3, 2, "#6b4a2a")

    pine(12, 42); pine(26, 33); pine(43, 25); palm(65, 37, 0.8)
    palm(175, 37, -0.8); pine(197, 25); pine(213, 34); pine(228, 44)


def banner():
    land_img = Image.new("RGB", (W, H), "#c9e4dc")
    scene(ImageDraw.Draw(land_img), random.Random(11))
    img = Image.new("RGB", (W, H + 10), "#c9e4dc")  # the scene sits 10 rows lower so the lighthouse clears the title
    img.paste(land_img, (0, 10))
    d = ImageDraw.Draw(img)
    title = "SNAP SAFE INDIA"
    text(d, (W - width(title, 2)) // 2, 7, title, "#0b2624", 2, shadow="#f3f8f5")
    tag = "PHOTO PRIVACY AGENT FOR INDIA"
    text(d, (W - width(tag, 1)) // 2, 26, tag, "#35504d", 1)
    img.resize((W * SCALE, (H + 10) * SCALE), Image.NEAREST).save(OUT / "banner.png")


def divider():
    """A one-pixel-high-wave strip: stepped waves in the sea colours, 240 wide, scaled 5x."""
    img = Image.new("RGB", (W, 5), "#f3f8f5")
    d = ImageDraw.Draw(img)
    for x in range(W):
        y = 1 + round(1.2 * math.sin(x / 3.2))
        d.point((x, y), fill="#8fbab6"); d.point((x, y + 1), fill="#b2d3cf"); d.point((x, y + 2), fill="#cfe3de")
    for x in range(4, W, 20):
        d.rectangle([x, 0, x + 1, 0], fill="#d4483f")
    img.resize((W * SCALE, 5 * SCALE), Image.NEAREST).save(OUT / "divider.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    banner()
    divider()
    print("wrote", OUT / "banner.png", OUT / "divider.png")
