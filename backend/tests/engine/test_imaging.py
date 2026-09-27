"""Tests for app.engine.imaging (TSK-015)."""

import io

import pytest
from PIL import Image

from app.engine import imaging
from app.engine.constants import MAX_IMAGE_BYTES, NORMALIZED_SIZE
from app.engine.hasher import compute_hashes, hamming
from app.engine.imaging import InvalidImage, load_image, normalize, normalize_image
from tests.engine.imagegen import png_bytes, sneaker_logo

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def test_normalize_returns_rgb_square_of_requested_size():
    out = normalize(Image.new("RGB", (300, 120), (200, 0, 0)))
    assert out.mode == "RGB"
    assert out.size == (NORMALIZED_SIZE, NORMALIZED_SIZE)


def test_transparent_background_becomes_white_not_black():
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    img.paste((10, 10, 10, 255), (40, 40, 60, 60))
    out = normalize(img)
    assert out.getpixel((2, 2)) == WHITE
    assert out.getpixel((NORMALIZED_SIZE // 2, NORMALIZED_SIZE // 2)) == (10, 10, 10)


def test_palette_transparency_is_flattened():
    img = Image.new("P", (50, 50), 0)
    img.putpalette([0, 0, 0] + [255, 0, 0] * 255)
    img.info["transparency"] = 0
    assert normalize(img).getpixel((1, 1)) == WHITE


def test_transparent_logo_matches_same_logo_on_white():
    """Regression for v1: an RGBA logo used to hash against a black background."""
    logo = sneaker_logo()
    mask = Image.new("L", logo.size, 0)
    mask.paste(255, (40, 40, 370, 370))
    transparent = logo.convert("RGBA")
    transparent.putalpha(mask)
    on_white = Image.new("RGB", logo.size, WHITE)
    on_white.paste(logo.crop((40, 40, 370, 370)), (40, 40))

    flattened = compute_hashes(normalize_image(png_bytes(transparent)))
    reference = compute_hashes(normalize(on_white))
    naive = compute_hashes(normalize(transparent.convert("RGB")))   # v1 behaviour: black background

    assert hamming(flattened.phash, reference.phash) <= 2
    assert hamming(naive.phash, reference.phash) > hamming(flattened.phash, reference.phash)


def test_letterbox_pads_with_white_and_keeps_content_centred():
    out = normalize(Image.new("RGB", (300, 100), (200, 0, 0)))
    assert out.getpixel((NORMALIZED_SIZE // 2, 5)) == WHITE              # padded band above
    assert out.getpixel((NORMALIZED_SIZE // 2, NORMALIZED_SIZE // 2)) == (200, 0, 0)


def test_exif_orientation_is_applied():
    img = Image.new("RGB", (200, 100), WHITE)
    img.paste(BLACK, (0, 0, 100, 100))                                   # left half black
    exif = Image.Exif()
    exif[0x0112] = 6                                                     # "rotate 90 CW to display"
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif, quality=95)

    out = normalize_image(buf.getvalue())
    centre_x = NORMALIZED_SIZE // 2
    assert sum(out.getpixel((centre_x, 40))) < 60                       # left half is now on top
    assert sum(out.getpixel((centre_x, NORMALIZED_SIZE - 40))) > 700


@pytest.mark.parametrize("data", [b"", b"not an image at all", png_bytes(sneaker_logo())[:200]])
def test_invalid_bytes_raise_invalid_image(data):
    with pytest.raises(InvalidImage):
        load_image(data)


def test_oversized_bytes_are_rejected_before_decoding():
    with pytest.raises(InvalidImage, match="larger"):
        load_image(b"\x89PNG" + b"0" * MAX_IMAGE_BYTES)


def test_pixel_limit_guards_against_decompression_bombs(monkeypatch):
    monkeypatch.setattr(imaging, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(InvalidImage, match="pixels"):
        load_image(png_bytes(Image.new("RGB", (20, 20))))


def test_invalid_image_is_a_value_error():
    assert issubclass(InvalidImage, ValueError)
