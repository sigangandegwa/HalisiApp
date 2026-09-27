"""Engine constants: image limits and visual-similarity calibration.

Every value here is a scoring heuristic. Changing one requires a new version row in
AGENTS.md section 7.2 (Prompt & Heuristic Registry).

The visual thresholds are starting values (HASH_SIMILARITY v2, CLIP_SIMILARITY v1). They are
calibrated against the seed logo variants in TSK-017 and the results recorded in docs/calibration.md.
Scorer weights and verdict thresholds are added here by TSK-008.
"""

from typing import Final

# --- Image normalisation (imaging.py) ---------------------------------------------------------
MAX_IMAGE_BYTES: Final = 5 * 1024 * 1024       # reject larger uploads / downloads
MAX_IMAGE_PIXELS: Final = 25_000_000            # decompression-bomb guard (width * height)
NORMALIZED_SIZE: Final = 256                    # square side after normalisation
PAD_COLOR: Final = (255, 255, 255)              # alpha flatten + letterbox colour

# --- Perceptual hashing (hasher.py): HASH_SIMILARITY v2 ---------------------------------------
HASH_SIZE: Final = 8                            # 8x8 -> 64-bit hashes, 16 hex chars
HASH_BITS: Final = HASH_SIZE * HASH_SIZE
HASH_FULL_MATCH_BITS: Final = 4                 # Hamming distance <= this -> similarity 100
HASH_NO_MATCH_BITS: Final = 24                  # Hamming distance >= this -> similarity 0
# Unrelated images average ~32 differing bits (each bit is roughly a coin flip), so v1's
# `100 - d/64*100` gave them ~50 %. The linear ramp between 4 and 24 puts them at 0.

# --- CLIP embeddings: CLIP_SIMILARITY v1 -------------------------------------------------------
CLIP_FULL_MATCH_COSINE: Final = 0.93            # cosine >= this -> similarity 100
CLIP_NO_MATCH_COSINE: Final = 0.80              # cosine <= this -> similarity 0
