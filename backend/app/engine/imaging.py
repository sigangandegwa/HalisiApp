"""Image decoding and normalisation for the detection engine.

Pure functions: bytes or PIL images in, normalised PIL images out. No network, no DB.
Downloading images (with the SSRF guard and size cap) belongs in ingestion/, not here.
"""

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.engine.constants import MAX_IMAGE_BYTES, MAX_IMAGE_PIXELS, NORMALIZED_SIZE, PAD_COLOR


class InvalidImage(ValueError):
    """Raised when bytes are not a decodable, reasonably sized image."""


def load_image(data: bytes) -> Image.Image:
    """Decode image bytes into a fully loaded PIL image.

    Enforces the byte and pixel limits before decoding pixel data, and runs Pillow's
    structural ``verify()`` first (which invalidates the file, so the image is reopened).

    Raises:
        InvalidImage: empty, too large, too many pixels, or not a supported image.
    """
    if not data:
        raise InvalidImage("Image is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise InvalidImage(f"Image is larger than {MAX_IMAGE_BYTES} bytes.")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.width * probe.height > MAX_IMAGE_PIXELS:
                raise InvalidImage(f"Image exceeds {MAX_IMAGE_PIXELS} pixels.")
            probe.verify()
        image = Image.open(io.BytesIO(data))
        image.load()
    except InvalidImage:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidImage("Not a valid image.") from exc
    return image


def normalize(image: Image.Image, size: int = NORMALIZED_SIZE) -> Image.Image:
    """Return an EXIF-upright RGB square of ``size`` px with transparency flattened onto white.

    Steps, in order:
      1. apply the EXIF orientation (phone photos are often stored sideways)
      2. flatten any transparency onto white. Transparent PNG logos otherwise hash against a
         black background and never match the same logo used as an avatar.
      3. letterbox to a square on white, keeping the aspect ratio (avatars are square, logos often aren't)
      4. resize with LANCZOS
    """
    upright = ImageOps.exif_transpose(image)
    rgb = _flatten_alpha(upright)
    square = _pad_to_square(rgb)
    if square.size != (size, size):
        square = square.resize((size, size), Image.Resampling.LANCZOS)
    return square


def normalize_image(data: bytes, size: int = NORMALIZED_SIZE) -> Image.Image:
    """Decode and normalise image bytes in one step. See :func:`load_image` and :func:`normalize`."""
    return normalize(load_image(data), size)


def _flatten_alpha(image: Image.Image) -> Image.Image:
    """Composite any transparency onto ``PAD_COLOR`` and return an RGB image."""
    if not image.has_transparency_data:
        return image.convert("RGB")
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (*PAD_COLOR, 255))
    background.alpha_composite(rgba)
    return background.convert("RGB")


def _pad_to_square(image: Image.Image) -> Image.Image:
    """Centre ``image`` on a square ``PAD_COLOR`` canvas whose side is its longest edge."""
    width, height = image.size
    if width == height:
        return image
    side = max(width, height)
    canvas = Image.new("RGB", (side, side), PAD_COLOR)
    canvas.paste(image, ((side - width) // 2, (side - height) // 2))
    return canvas
