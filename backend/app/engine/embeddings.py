"""Optional CLIP ViT-B-32 image embeddings (TSK-017 code part, docs/BACKEND.md section 6.3).

* Loaded lazily, once, and only when ``ENABLE_CLIP=true``. ``sentence-transformers`` / ``torch``
  live in ``requirements-ml.txt`` and are imported only inside :meth:`ClipEmbedder.load`.
* When disabled or unavailable every call returns ``None`` and the visual score falls back to
  pHash/dHash, so the same code path works with or without the model.
* Calls are CPU/GPU bound: the API calls :meth:`ClipEmbedder.embed_async` (``asyncio.to_thread``).
* Tests inject a fake model (anything with ``encode(images, normalize_embeddings=True)``).
"""

import asyncio
import logging
from collections.abc import Callable, Sequence
from typing import Any, Protocol

from PIL import Image

log = logging.getLogger("halisi.engine.clip")
EMBEDDING_DIM = 512


class EncoderModel(Protocol):
    """The subset of ``SentenceTransformer`` we use."""

    def encode(self, sentences: Any, **kwargs: Any) -> Any: ...


def _default_loader(model_name: str, device: str) -> EncoderModel:
    """Import sentence-transformers and load the model (downloads weights on first use)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, device=device)


def _auto_device(requested: str) -> str:
    """``cuda`` when available and not forced to CPU, else ``cpu``."""
    if requested == "cpu":
        return "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    if requested == "cuda":
        log.warning("ENGINE_DEVICE=cuda requested but CUDA is unavailable; using cpu")
    return "cpu"


class ClipEmbedder:
    """Holds the (optional) CLIP model. ``status`` is ``disabled`` / ``cpu`` / ``cuda`` / ``error``."""

    def __init__(
        self,
        enabled: bool,
        model_name: str = "clip-ViT-B-32",
        device: str = "auto",
        *,
        model: EncoderModel | None = None,
        loader: Callable[[str, str], EncoderModel] = _default_loader,
        device_resolver: Callable[[str], str] = _auto_device,
    ) -> None:
        self.enabled = enabled
        self.model_name = model_name
        self.requested_device = device
        self._model = model
        self._loader = loader
        self._device_resolver = device_resolver
        self.device: str | None = "injected" if model is not None else None
        self.error: str | None = None

    @property
    def status(self) -> str:
        """Health string for ``/health``."""
        if not self.enabled:
            return "disabled"
        if self.error:
            return "error"
        return self.device or "not_loaded"

    @property
    def ready(self) -> bool:
        """Whether embeddings will be produced."""
        return self.enabled and self._model is not None and self.error is None

    def load(self) -> None:
        """Load the model once. Failures are logged and leave the engine in hash-only mode."""
        if not self.enabled or self._model is not None:
            return
        try:
            self.device = self._device_resolver(self.requested_device)
            self._model = self._loader(self.model_name, self.device)
        except Exception as exc:  # noqa: BLE001 - any import/load failure means hash-only mode
            self.error = f"{type(exc).__name__}: {exc}"
            log.warning("CLIP unavailable, falling back to hashes only: %s", self.error)

    def warm_up(self) -> None:
        """Load and run one dummy image so the first (slow) CUDA call never lands on a judge."""
        self.load()
        if self.ready:
            self.embed(Image.new("RGB", (224, 224), (255, 255, 255)))

    def embed(self, image: Image.Image) -> list[float] | None:
        """512-d L2-normalised embedding, or None when CLIP is disabled/unavailable/failing."""
        if not self.ready:
            return None
        try:
            vectors = self._model.encode([image], normalize_embeddings=True)  # type: ignore[union-attr]
            return _to_list(vectors[0])
        except Exception as exc:  # noqa: BLE001 - never fail a check because CLIP failed
            log.warning("CLIP embedding failed: %r", exc)
            return None

    async def embed_async(self, image: Image.Image) -> list[float] | None:
        """:meth:`embed` in a worker thread."""
        if not self.ready:
            return None
        return await asyncio.to_thread(self.embed, image)


def _to_list(vector: Any) -> list[float]:
    """numpy / torch / list -> list[float]."""
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    values: Sequence[float] = vector
    return [float(v) for v in values]
