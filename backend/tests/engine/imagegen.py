"""Deterministic synthetic logos and clone-style edits for engine tests (no network, no files)."""

import io

from PIL import Image, ImageDraw, ImageOps

SIZE = 400


def sneaker_logo() -> Image.Image:
    """Navy disc with a white diagonal stripe and a gold heel block: stands in for 'Nairobi Sneaker Vault'."""
    img = Image.new("RGB", (SIZE, SIZE), (250, 248, 240))
    d = ImageDraw.Draw(img)
    d.ellipse((40, 40, 300, 300), fill=(20, 40, 110))
    d.polygon([(60, 250), (250, 60), (290, 100), (100, 290)], fill=(250, 248, 240))
    d.rectangle((250, 280, 370, 370), fill=(210, 160, 30))
    return img


def glow_logo() -> Image.Image:
    """Pink horizontal bands on dark plum: stands in for 'Kilimani Glow'."""
    img = Image.new("RGB", (SIZE, SIZE), (60, 20, 50))
    d = ImageDraw.Draw(img)
    for i, y in enumerate(range(30, SIZE, 80)):
        d.rectangle((0 if i % 2 else 120, y, SIZE if i % 2 else 380, y + 36), fill=(240, 140, 180))
    return img


def threads_logo() -> Image.Image:
    """Teal concentric squares, bright bottom-left corner: stands in for 'Pwani Threads'."""
    img = Image.new("RGB", (SIZE, SIZE), (0, 110, 120))
    d = ImageDraw.Draw(img)
    for i, inset in enumerate(range(20, 200, 40)):
        width = 14 if i % 2 else 6
        d.rectangle((inset, inset, SIZE - inset, SIZE - inset), outline=(230, 250, 245), width=width)
    d.rectangle((0, 300, 100, SIZE), fill=(255, 230, 120))
    return img


ALL_LOGOS = {"sneaker": sneaker_logo, "glow": glow_logo, "threads": threads_logo}


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
    """Encode as PNG bytes (keeps alpha)."""
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()
