"""Deterministic synthetic logos and clone-style edits (seed data + hash/CLIP calibration set).

Flat-colour logos with a little text hash almost alike, so each design uses large, distinct shapes.
The three merchant designs were moved here from ``tests/engine/imagegen.py`` (which re-exports them),
so engine tests and seed data use the exact same pixels. Everything is generated in code: no downloads.
"""

import io

from PIL import Image, ImageDraw, ImageOps

SIZE = 400


# --- merchant logos (fictional businesses) ------------------------------------------------------


def sneaker_logo() -> Image.Image:
    """Navy disc with a white diagonal stripe and a gold heel block: 'Nairobi Sneaker Vault'."""
    img = Image.new("RGB", (SIZE, SIZE), (250, 248, 240))
    d = ImageDraw.Draw(img)
    d.ellipse((40, 40, 300, 300), fill=(20, 40, 110))
    d.polygon([(60, 250), (250, 60), (290, 100), (100, 290)], fill=(250, 248, 240))
    d.rectangle((250, 280, 370, 370), fill=(210, 160, 30))
    return img


def glow_logo() -> Image.Image:
    """Pink horizontal bands on dark plum: 'Kilimani Glow'."""
    img = Image.new("RGB", (SIZE, SIZE), (60, 20, 50))
    d = ImageDraw.Draw(img)
    for i, y in enumerate(range(30, SIZE, 80)):
        d.rectangle((0 if i % 2 else 120, y, SIZE if i % 2 else 380, y + 36), fill=(240, 140, 180))
    return img


def threads_logo() -> Image.Image:
    """Teal concentric squares, bright bottom-left corner: 'Pwani Threads'."""
    img = Image.new("RGB", (SIZE, SIZE), (0, 110, 120))
    d = ImageDraw.Draw(img)
    for i, inset in enumerate(range(20, 200, 40)):
        width = 14 if i % 2 else 6
        d.rectangle((inset, inset, SIZE - inset, SIZE - inset), outline=(230, 250, 245), width=width)
    d.rectangle((0, 300, 100, SIZE), fill=(255, 230, 120))
    return img


# --- look-alike legitimate competitors (their OWN logos) ----------------------------------------


def hub_logo() -> Image.Image:
    """Orange upward triangle over a charcoal bar: 'Nairobi Sneaker Hub' (competitor)."""
    img = Image.new("RGB", (SIZE, SIZE), (235, 235, 235))
    d = ImageDraw.Draw(img)
    d.polygon([(200, 30), (370, 300), (30, 300)], fill=(240, 110, 20))
    d.rectangle((30, 320, 370, 380), fill=(40, 40, 45))
    return img


def beauty_logo() -> Image.Image:
    """Green vertical pillars with a cream top band: 'Kilimani Beauty Bar' (competitor)."""
    img = Image.new("RGB", (SIZE, SIZE), (250, 245, 225))
    d = ImageDraw.Draw(img)
    for x in range(40, SIZE - 40, 90):
        d.rectangle((x, 120, x + 45, 380), fill=(30, 120, 70))
    d.rectangle((0, 0, SIZE, 70), fill=(200, 170, 90))
    return img


def coast_logo() -> Image.Image:
    """Red and white checkerboard quadrant with a blue wave: 'Pwani Fashion House' (competitor)."""
    img = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for row in range(4):
        for col in range(4):
            if (row + col) % 2 == 0:
                d.rectangle((col * 50, row * 50, col * 50 + 49, row * 50 + 49), fill=(200, 30, 45))
    d.ellipse((150, 200, 450, 500), fill=(20, 70, 160))
    return img


MERCHANT_LOGOS = {"sneaker": sneaker_logo, "glow": glow_logo, "threads": threads_logo}
COMPETITOR_LOGOS = {"hub": hub_logo, "beauty": beauty_logo, "coast": coast_logo}


# --- clone-style edits (what scammers actually do to a stolen logo) -----------------------------


def jpeg(img: Image.Image, quality: int = 35) -> Image.Image:
    """Heavy JPEG re-compression, as after a screenshot + re-upload."""
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def downscale(img: Image.Image, side: int = 64) -> Image.Image:
    """Shrink to a thumbnail and blow back up (low-res avatar grab)."""
    return img.resize((side, side), Image.Resampling.BILINEAR).resize(img.size, Image.Resampling.BILINEAR)


def overlay_text(img: Image.Image, text: str = "OFFICIAL") -> Image.Image:
    """Stamp a small caption in a corner ("OFFICIAL", "KE")."""
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.rectangle((250, 12, 390, 52), fill=(200, 30, 30))
    d.text((262, 22), text, fill=(255, 255, 255))
    return out


def crop(img: Image.Image, keep: float = 0.85) -> Image.Image:
    """Centre-crop to ``keep`` of each side, then resize back."""
    w, h = img.size
    dx, dy = int(w * (1 - keep) / 2), int(h * (1 - keep) / 2)
    return img.crop((dx, dy, w - dx, h - dy)).resize(img.size, Image.Resampling.LANCZOS)


def recolor(img: Image.Image) -> Image.Image:
    """Swap colour channels: same shapes, different palette."""
    r, g, b = img.split()
    return Image.merge("RGB", (b, r, g))


def invert(img: Image.Image) -> Image.Image:
    """Negative image (light/dark swapped)."""
    return ImageOps.invert(img)


def png_bytes(img: Image.Image) -> bytes:
    """Encode as PNG bytes (keeps alpha). Deterministic for the same pixels."""
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=False)
    return buf.getvalue()


EDITS = {"jpeg": jpeg, "downscale": downscale, "overlay": overlay_text, "crop": crop, "recolor": recolor}
