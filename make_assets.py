"""Generates the default owl artwork (assets/owl.png and assets/owl.ico).

This is a placeholder illustration. For the realistic look, drop any owl photograph
(PNG with a transparent or dark background works best) into assets/owl.png - the app
rescales it automatically.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

S = 4                      # supersampling factor
W, H = 520 * S, 600 * S
random.seed(7)


def P(v):
    return int(v * S)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def radial(size, inner, outer, center=None, power=1.0):
    w, h = size
    cx, cy = center or (w / 2, h / 2)
    img = Image.new("RGB", size)
    px = img.load()
    rmax = math.hypot(max(cx, w - cx), max(cy, h - cy))
    for y in range(h):
        for x in range(w):
            t = min(1.0, (math.hypot(x - cx, y - cy) / rmax) ** power)
            px[x, y] = lerp(inner, outer, t)
    return img


def ellipse_mask(box):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return m


def paste_gradient(canvas, box, inner, outer, power=0.9, blur=0):
    x0, y0, x1, y1 = [P(v) for v in box]
    g = radial((x1 - x0, y1 - y0), inner, outer, power=power)
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, x1 - x0 - 1, y1 - y0 - 1), fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(g, (x0, y0), mask)


def feathers(draw, box, base, count, size, jitter=18):
    x0, y0, x1, y1 = box
    for _ in range(count):
        x, y = random.uniform(x0, x1), random.uniform(y0, y1)
        # keep inside the ellipse
        if ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 2 + ((y - (y0 + y1) / 2) / ((y1 - y0) / 2)) ** 2 > 1:
            continue
        shade = random.randint(-jitter, jitter)
        col = tuple(max(0, min(255, c + shade)) for c in base)
        w = size * random.uniform(0.8, 1.2)
        draw.arc((P(x - w), P(y - w * 0.6), P(x + w), P(y + w * 0.9)), 20, 160, fill=col, width=max(1, P(1.6)))


def build() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rgb = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(rgb)
    mask_all = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask_all)

    # ear tufts
    for sign in (-1, 1):
        cx = 260 + sign * 120
        pts = [(cx - sign * 40, 150), (cx + sign * 25, 40), (cx + sign * 60, 170)]
        d.polygon([(P(x), P(y)) for x, y in pts], fill=(92, 62, 38))
        md.polygon([(P(x), P(y)) for x, y in pts], fill=255)

    # body
    body = (80, 170, 440, 590)
    paste_gradient(rgb, body, (176, 128, 80), (62, 40, 26), power=0.85)
    md.ellipse([P(v) for v in body], fill=255)
    # head
    head = (92, 70, 428, 380)
    paste_gradient(rgb, head, (170, 124, 78), (70, 46, 30), power=0.9)
    md.ellipse([P(v) for v in head], fill=255)

    # chest feather texture
    feathers(d, (140, 330, 380, 580), (214, 178, 130), 330, 13)
    feathers(d, (92, 70, 428, 380), (60, 40, 26), 260, 10, 14)
    # wings
    for sign in (-1, 1):
        wing = (260 + sign * 150 - 52, 300, 260 + sign * 150 + 52, 570)
        paste_gradient(rgb, wing, (110, 76, 48), (42, 28, 18), power=0.8)
        md.ellipse([P(v) for v in wing], fill=255)
        feathers(d, wing, (28, 18, 12), 80, 9)

    # facial discs
    for sign in (-1, 1):
        disc = (260 + sign * 80 - 88, 130, 260 + sign * 80 + 88, 320)
        paste_gradient(rgb, disc, (240, 220, 186), (170, 132, 92), power=1.1)
    d.arc((P(92), P(110), P(428), P(350)), 0, 360, fill=(70, 46, 30), width=P(4))

    # eyes
    for sign in (-1, 1):
        cx, cy = 260 + sign * 76, 215
        r = 50
        paste_gradient(rgb, (cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), (30, 20, 14), (10, 6, 4), power=1.5)
        paste_gradient(rgb, (cx - r, cy - r, cx + r, cy + r), (255, 196, 40), (214, 110, 10), power=0.9)
        pr = 24
        d.ellipse((P(cx - pr), P(cy - pr), P(cx + pr), P(cy + pr)), fill=(6, 4, 4))
        d.ellipse((P(cx - 13 + sign * -3), P(cy - 17), P(cx - 1 + sign * -3), P(cy - 5)), fill=(255, 255, 255))
        # stern brow
        brow = [(cx - sign * 60, cy - 62 + (14 if sign == -1 else 0) * 0),
                (cx + sign * 58, cy - 30), (cx + sign * 58, cy - 46), (cx - sign * 62, cy - 78)]
        d.polygon([(P(x), P(y)) for x, y in [(cx - sign * 62, cy - 40), (cx + sign * 4, cy - 66),
                                             (cx + sign * 58, cy - 8 - 30), (cx - sign * 62, cy - 68)]],
                  fill=(58, 38, 24))

    # beak
    beak = [(P(238), P(250)), (P(282), P(250)), (P(260), P(312))]
    d.polygon(beak, fill=(196, 150, 70))
    d.line([(P(260), P(262)), (P(260), P(306))], fill=(120, 84, 36), width=P(2))

    # feet
    for sign in (-1, 1):
        for k in range(3):
            x = 260 + sign * 52 + (k - 1) * 18
            d.rounded_rectangle((P(x - 8), P(560), P(x + 8), P(592)), radius=P(8), fill=(188, 142, 62))

    img = Image.composite(rgb.convert("RGBA"), img, mask_all)
    # soft vignette/shadow for depth
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(mask_all.filter(ImageFilter.GaussianBlur(P(8))).point(lambda v: int(v * 0.0)))
    return img.resize((W // S, H // S), Image.LANCZOS)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    owl = build()
    owl.save(out / "owl.png")
    ico = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    thumb = owl.copy()
    thumb.thumbnail((250, 250), Image.LANCZOS)
    ico.paste(thumb, ((256 - thumb.width) // 2, (256 - thumb.height) // 2), thumb)
    ico.save(out / "owl.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", out / "owl.png", out / "owl.ico")
