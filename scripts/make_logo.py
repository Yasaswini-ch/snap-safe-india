"""Cut the site's icons out of the Snap Safe India logo (static/logo.png, the full lockup with the name).

Writes static/mark.png (the camera and shield alone, for the page header), favicon.png (32), apple-touch-icon.png (180),
icon-192.png and icon-512.png. The app icons keep the camera and shield inside the middle 80% so a phone can mask them
to a circle. To change the logo, replace static/logo.png and run:

Usage: uv run python scripts/make_logo.py
"""
from pathlib import Path

from PIL import Image

STATIC = Path(__file__).parent.parent / "static"
BACKGROUND = (254, 253, 249)  # the logo's off-white
EMBLEM = (120, 180, 1165, 810)  # camera, brackets, shield and cards, in the 1254 px source
CAMERA = (240, 235, 1010, 800)  # the camera and shield without the brackets and cards: the page header
LENS = (410, 320, 1010, 790)  # the lens with the map and the shield: what stays readable at 32 px


def square(img: Image.Image, box: tuple, side: int) -> Image.Image:
    """`box` centred on a background-coloured square of `side` source pixels (the box may sit near an edge)."""
    cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    canvas = Image.new("RGB", (side, side), BACKGROUND)
    canvas.paste(img.crop(box), (side // 2 - (cx - box[0]), side // 2 - (cy - box[1])))
    return canvas


def main():
    logo = Image.open(STATIC / "logo.png").convert("RGB")
    k = logo.width / 1254  # the boxes above are for the 1254 px original
    scale = lambda b: tuple(round(v * k) for v in b)  # noqa: E731
    emblem, lens = scale(EMBLEM), scale(LENS)
    for name, size in (("icon-512", 512), ("icon-192", 192), ("apple-touch-icon", 180)):
        square(logo, emblem, round(1300 * k)).resize((size, size), Image.LANCZOS).save(STATIC / f"{name}.png")
    square(logo, scale(CAMERA), round(800 * k)).resize((128, 128), Image.LANCZOS).save(STATIC / "mark.png")
    square(logo, lens, round(640 * k)).resize((32, 32), Image.LANCZOS).save(STATIC / "favicon.png")
    print("wrote mark.png, favicon.png, apple-touch-icon.png, icon-192.png and icon-512.png in static/")


if __name__ == "__main__":
    main()
