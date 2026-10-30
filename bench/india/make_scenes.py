"""Indian benchmark scenes, rendered with Pillow: staged, fictional, and clearly not real photos or real documents.

Every name, number and address below is made up. The cards are generic layouts marked SAMPLE, not copies of any official
document. Each scene is a document, plate or sign placed in a slightly rotated, noisy "phone photo" frame.
ground truth = the strings in `secrets`; `expect` = the text-check kinds (app/regions) that should fire on the scene.

Usage: uv run python -m bench.india.make_scenes
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent
IMAGES = OUT / "images"
SIZE = (1280, 960)


def font(size, bold=False):
    return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)


def telugu(size):
    return ImageFont.truetype("Nirmala.ttc", size)


def surface(rng, base, streak=10):
    """A table or wall: a base colour with horizontal streaks and low-frequency blotches."""
    w, h = SIZE
    rows = rng.normal(0, streak, (h, 1, 1)) + np.zeros((h, w, 3))
    blot = np.asarray(Image.fromarray(rng.integers(0, 255, (12, 16), dtype=np.uint8)).resize(SIZE, Image.BICUBIC))
    arr = np.array(base, float) + rows + (blot[..., None] - 128) * 0.12
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def photo(items, seed, base=(150, 110, 75), angle=0.0, name="x"):
    """items: [(PIL image, (x, y))] pasted onto a surface with a soft shadow, then phone-photo noise and blur."""
    rng = np.random.default_rng(seed)
    canvas = surface(rng, base)
    for img, (x, y) in items:
        img = img.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow.putalpha(img.getchannel("A").point(lambda a: 110 if a else 0))
        canvas.paste(shadow.filter(ImageFilter.GaussianBlur(10)), (x + 10, y + 14), shadow.filter(ImageFilter.GaussianBlur(10)))
        canvas.paste(img, (x, y), img)
    return finish(canvas, rng, name)


def finish(canvas, rng, name):
    img = canvas.filter(ImageFilter.GaussianBlur(0.8))
    arr = np.asarray(img).astype(float)
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    vignette = 1 - 0.28 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2) * 2
    arr = arr * vignette[..., None] + rng.normal(0, 4, arr.shape)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(IMAGES / f"{name}.jpg", quality=88)


def paper(size, bg=(248, 246, 238), border=None):
    img = Image.new("RGBA", size, bg + (255,))
    if border:
        ImageDraw.Draw(img).rectangle([0, 0, size[0] - 1, size[1] - 1], outline=border, width=6)
    return img, ImageDraw.Draw(img)


def rows(d, x, y, items, gap=44, size=30, fill=(20, 20, 30)):
    for label, value in items:
        d.text((x, y), label, font=font(size - 6), fill=(110, 110, 120))
        d.text((x + 230, y), value, font=font(size, True), fill=fill)
        y += gap
    return y


def id_card():
    img, d = paper((820, 520), (236, 244, 252), (40, 80, 150))
    d.rectangle([0, 0, 820, 78], fill=(40, 80, 150))
    d.text((24, 18), "SAMPLE IDENTITY CARD", font=font(36, True), fill="white")
    d.rectangle([28, 110, 220, 330], fill=(190, 200, 215))
    d.ellipse([80, 130, 170, 220], fill=(150, 160, 175))
    rows(d, 250, 110, [("Name", "Ravi Teja Kondapalli"), ("DOB", "14/08/1999"),
                       ("Door No", "12-4/7, Gandhi Nagar"), ("City", "Visakhapatnam"), ("PIN", "530003")], 46, 28)
    d.text((250, 350), "2345 6789 0124", font=font(52, True), fill=(20, 20, 30))
    d.text((28, 470), "Sample card, all details fictional", font=font(20), fill=(110, 110, 120))
    return img


def pan_card():
    img, d = paper((820, 500), (244, 238, 224), (150, 110, 60))
    d.text((24, 20), "SAMPLE TAX CARD", font=font(36, True), fill=(110, 70, 30))
    rows(d, 40, 120, [("Name", "SNEHA REDDY MALLIPUDI"), ("Father", "KRISHNA REDDY MALLIPUDI"),
                      ("Born", "02/11/1997")], 56, 30)
    d.text((40, 320), "ABCDE1234F", font=font(64, True), fill=(20, 20, 30))
    d.text((40, 450), "Sample card, all details fictional", font=font(20), fill=(110, 110, 120))
    return img


def parcel_label():
    img, d = paper((760, 560), (255, 255, 255), (30, 30, 30))
    d.rectangle([0, 0, 760, 70], fill=(30, 30, 30))
    d.text((24, 14), "SAMPLE COURIER  |  PREPAID", font=font(34, True), fill="white")
    d.text((28, 100), "DELIVER TO:", font=font(22), fill=(110, 110, 120))
    for i, line in enumerate(["Sneha Reddy M", "Flat No 302, Sai Residency", "Siripuram, Visakhapatnam - 530003",
                              "Ph: 98765 43210"]):
        d.text((28, 136 + i * 46), line, font=font(32, i == 0), fill=(20, 20, 30))
    for i in range(46):
        d.rectangle([28 + i * 15, 380, 28 + i * 15 + (4 + i * 7 % 9), 500], fill=(20, 20, 30))
    d.text((28, 515), "AWB 7001 2345 6789", font=font(24), fill=(20, 20, 30))
    return img


def number_plate(rng):
    w, h = SIZE
    img = Image.new("RGB", SIZE, (170, 175, 165))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 640, w, h], fill=(95, 95, 98))  # road
    d.rectangle([0, 0, w, 640], fill=(196, 188, 170))  # compound wall
    d.rounded_rectangle([200, 250, 1080, 700], 60, fill=(150, 30, 35))  # car body, rear
    d.rounded_rectangle([300, 120, 980, 330], 70, fill=(120, 24, 28))
    d.rounded_rectangle([340, 150, 940, 305], 40, fill=(60, 80, 100))  # rear glass
    for x in (215, 985):
        d.rounded_rectangle([x, 330, x + 80, 420], 20, fill=(220, 40, 40))  # tail lights
    d.rounded_rectangle([470, 470, 810, 570], 12, fill=(250, 250, 250), outline=(20, 20, 20), width=6)
    d.text((490, 484), "AP 31 AB 1234", font=font(58, True), fill=(20, 20, 20))
    d.ellipse([260, 640, 420, 800], fill=(25, 25, 25))
    d.ellipse([860, 640, 1020, 800], fill=(25, 25, 25))
    finish(img, rng, "car_plate_in")


def house_board():
    img, d = paper((900, 460), (30, 30, 34), (200, 170, 90))
    d.text((60, 40), "Door No. 7-19-3", font=font(54, True), fill=(225, 190, 100))
    d.text((60, 140), "Sri Venkata Ramana Nilayam", font=font(60, True), fill=(225, 190, 100))
    d.text((60, 250), "MVP Colony, Visakhapatnam", font=font(48), fill=(225, 190, 100))
    d.text((60, 340), "Dr. V. Ramana Murthy, MBBS", font=font(40), fill=(225, 190, 100))
    return img


def upi_screen():
    img = Image.new("RGBA", (520, 940), (20, 20, 24, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([16, 16, 504, 924], 40, fill=(255, 255, 255))
    d.ellipse([200, 90, 320, 210], fill=(60, 170, 90))
    d.text((150, 240), "Payment successful", font=font(34, True), fill=(30, 30, 30))
    d.text((190, 300), "Rs. 1,250", font=font(54, True), fill=(30, 30, 30))
    for i, (a, b) in enumerate([("Paid to", "Asha Kumari"), ("UPI ID", "asha.k@okhdfcbank"),
                                ("Ref no", "4012 3456 7890"), ("From", "SBI  ****4821")]):
        d.text((50, 430 + i * 90), a, font=font(24), fill=(120, 120, 128))
        d.text((50, 462 + i * 90), b, font=font(32, True), fill=(30, 30, 30))
    return img


def telugu_sign(rng):
    img = Image.new("RGB", SIZE, (150, 70, 55))
    d = ImageDraw.Draw(img)
    for y in range(0, SIZE[1], 40):  # brick wall
        for x in range(-60 if (y // 40) % 2 else 0, SIZE[0], 120):
            d.rectangle([x + 3, y + 3, x + 117, y + 37], fill=(165 + int(rng.integers(0, 25)), 80, 62))
    d.rounded_rectangle([140, 230, 1140, 640], 30, fill=(20, 70, 150), outline="white", width=10)
    d.text((220, 290), "శ్రీ సాయి మెడికల్స్", font=telugu(88), fill="white")
    d.text((220, 440), "Sri Sai Medicals", font=font(70, True), fill="white")
    d.text((220, 550), "Cell: 99999 12345    Siripuram", font=font(48), fill=(255, 220, 120))
    finish(img, rng, "telugu_sign")


def college_lanyard():
    img, d = paper((520, 760), (255, 255, 255), (150, 30, 40))
    d.rectangle([0, 0, 520, 120], fill=(150, 30, 40))
    d.text((24, 20), "SAMPLE ENGINEERING", font=font(34, True), fill="white")
    d.text((24, 66), "COLLEGE, VIZAG", font=font(34, True), fill="white")
    d.rectangle([160, 160, 360, 400], fill=(190, 200, 215))
    d.ellipse([220, 180, 300, 260], fill=(150, 160, 175))
    d.text((40, 430), "Lakshmi Prasanna Gadde", font=font(34, True), fill=(20, 20, 30))
    d.text((40, 490), "B.Tech CSE, 3rd year", font=font(28), fill=(60, 60, 70))
    d.text((40, 560), "Roll No: 21A91A0512", font=font(34, True), fill=(20, 20, 30))
    d.text((40, 640), "Hostel: Block C, Room 214", font=font(28), fill=(60, 60, 70))
    return img


def wedding_invite():
    img, d = paper((760, 900), (255, 236, 200), (170, 40, 40))
    d.text((190, 50), "Subhamastu", font=font(56, True), fill=(160, 30, 30))
    for i, line in enumerate(["Chi. Kiran Kumar", "weds", "Chi.Sow. Divya", "Muhurtham: 14-12-2026, 10:42 AM",
                              "Venue: Sri Lakshmi Kalyana Mandapam", "Dwaraka Nagar, Visakhapatnam",
                              "RSVP: 90000 12345"]):
        d.text((60, 190 + i * 90), line, font=font(40, i in (0, 2)), fill=(70, 30, 20))
    return img


def tea_menu(rng):
    img = Image.new("RGB", SIZE, (28, 40, 34))
    d = ImageDraw.Draw(img)
    d.text((120, 90), "TEA STALL MENU", font=font(96, True), fill=(235, 235, 225))
    for i, line in enumerate(["Chai ........ Rs 10", "Coffee ...... Rs 15", "Samosa ..... Rs 15", "Biscuit ..... Rs 5"]):
        d.text((160, 280 + i * 120), line, font=font(70), fill=(225, 225, 215))
    finish(img, rng, "ctrl_tea_menu")


# Run by default: a spread of scenes plus the control. The other five are for extra runs (bench.indiabench --all).
CORE = {"id_card", "parcel_label", "car_plate_in", "telugu_sign", "ctrl_tea_menu"}

SCENES = [
    ("id_card", "leak", ["Ravi Teja Kondapalli", "2345 6789 0124", "12-4/7", "530003"], ["Aadhaar number", "PIN code"]),
    ("tax_card", "leak", ["SNEHA REDDY MALLIPUDI", "ABCDE1234F"], ["PAN number"]),
    ("parcel_label", "leak", ["Sneha Reddy", "Sai Residency", "98765 43210", "530003"],
     ["phone number", "PIN code", "street address"]),
    ("car_plate_in", "leak", ["AP 31 AB 1234"], ["vehicle plate"]),
    ("house_board", "leak", ["7-19-3", "Venkata Ramana", "MVP Colony"], ["street address"]),
    ("upi_screen", "leak", ["Asha Kumari", "asha.k@okhdfcbank"], ["UPI ID"]),
    ("telugu_sign", "leak", ["99999 12345", "Sri Sai Medicals", "శ్రీ సాయి మెడికల్స్"], ["phone number"]),
    ("college_lanyard", "leak", ["Lakshmi Prasanna Gadde", "21A91A0512", "Block C, Room 214"], []),
    ("wedding_invite", "leak", ["Kiran Kumar", "Divya", "Dwaraka Nagar", "90000 12345"], ["phone number"]),
    ("ctrl_tea_menu", "control", [], []),
]


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    number_plate(rng)
    telugu_sign(rng)
    tea_menu(rng)
    photo([(id_card(), (240, 220))], 1, (150, 110, 75), 4, "id_card")
    photo([(pan_card(), (230, 230))], 2, (90, 95, 105), -5, "tax_card")
    photo([(parcel_label(), (260, 190))], 3, (190, 160, 110), 3, "parcel_label")
    photo([(house_board(), (190, 250))], 4, (170, 160, 150), 0, "house_board")
    photo([(upi_screen(), (380, 10))], 5, (110, 85, 60), -4, "upi_screen")
    photo([(college_lanyard(), (380, 90))], 6, (85, 100, 90), 3, "college_lanyard")
    photo([(wedding_invite(), (260, 20))], 7, (130, 90, 70), 2, "wedding_invite")
    (OUT / "scenes.json").write_text(json.dumps(
        [{"id": i, "kind": k, "secrets": s, "expect": e, "core": i in CORE} for i, k, s, e in SCENES], ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"wrote {len(SCENES)} scenes to {IMAGES}")


if __name__ == "__main__":
    main()
