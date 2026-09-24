import io
import httpx
from PIL import Image
import imagehash
import logging

logger = logging.getLogger(__name__)

async def download_image(url: str) -> Image.Image:
    """
    Downloads an image from a given URL and returns a PIL Image object.
    Raises ValueError if download fails or image is invalid.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            return image
    except Exception as e:
        logger.error(f"Failed to download or open image from {url}: {str(e)}")
        raise ValueError(f"Invalid image or unreachable URL: {url}")

async def compute_phash(url: str) -> str:
    """
    Downloads an image from a URL and computes its perceptual hash (pHash).
    """
    image = await download_image(url)
    hash_value = imagehash.phash(image)
    return str(hash_value)

def compare_hashes(hash1: str, hash2: str) -> float:
    """
    Compares two perceptual hashes and returns a similarity score (0 to 100).
    A distance of 0 means 100% identical. 
    """
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        # The Hamming distance between two pHashes. Max distance for a 64-bit hash is 64.
        distance = h1 - h2
        
        # Normalize to a 0-100 score where 0 distance = 100% similarity
        similarity = max(0.0, 100.0 - (distance / 64.0) * 100.0)
        return round(similarity, 2)
    except Exception as e:
        logger.error(f"Error comparing hashes {hash1} and {hash2}: {str(e)}")
        return 0.0
