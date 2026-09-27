"""CLIP embeddings (TSK-017 code part) with an injected fake model: torch is never imported."""

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.engine.embeddings import ClipEmbedder
from app.engine.hasher import ImageFeatures, visual_score
from app.ingestion.fixtures import logos as L
from app.main import create_app
from tests.conftest import make_settings


class FakeClip:
    """Deterministic 'embedding': mean colour + a few pixel stats, L2-normalised, padded to 512-d."""

    def __init__(self) -> None:
        self.calls = 0

    def encode(self, images, normalize_embeddings: bool = True):
        self.calls += 1
        out = []
        for img in images:
            arr = np.asarray(img.convert("L").resize((16, 32)), dtype=float).ravel()
            vec = np.zeros(512)
            vec[: arr.size] = arr - arr.mean()
            norm = np.linalg.norm(vec) or 1.0
            out.append(vec / norm if normalize_embeddings else vec)
        return np.array(out)


def test_disabled_returns_none_and_never_loads() -> None:
    loaded = []
    clip = ClipEmbedder(False, loader=lambda name, device: loaded.append(name))  # type: ignore[arg-type,return-value]
    clip.warm_up()
    assert clip.embed(Image.new("RGB", (8, 8))) is None
    assert clip.status == "disabled" and loaded == []


def test_lazy_load_with_device_resolution() -> None:
    fake = FakeClip()
    seen = {}

    def loader(name: str, device: str) -> FakeClip:
        seen.update(name=name, device=device)
        return fake

    clip = ClipEmbedder(True, "clip-ViT-B-32", "auto", loader=loader, device_resolver=lambda _: "cuda")
    assert clip.status == "not_loaded"
    clip.warm_up()
    assert seen == {"name": "clip-ViT-B-32", "device": "cuda"} and clip.status == "cuda" and fake.calls == 1
    vector = clip.embed(L.sneaker_logo())
    assert vector is not None and len(vector) == 512
    assert abs(sum(v * v for v in vector) - 1.0) < 1e-6


def test_load_failure_means_hash_only_mode() -> None:
    def broken(name: str, device: str) -> FakeClip:
        raise ImportError("No module named 'torch'")

    clip = ClipEmbedder(True, loader=broken, device_resolver=lambda _: "cpu")
    clip.warm_up()
    assert clip.status == "error" and clip.embed(Image.new("RGB", (8, 8))) is None


async def test_embed_async_runs_in_a_thread() -> None:
    clip = ClipEmbedder(True, model=FakeClip())
    assert clip.status == "injected"
    assert len(await clip.embed_async(L.glow_logo())) == 512


def test_clip_signal_joins_the_visual_score() -> None:
    clip = ClipEmbedder(True, model=FakeClip())
    a = clip.embed(L.sneaker_logo())
    b = clip.embed(L.crop(L.sneaker_logo(), 0.95))
    result = visual_score(ImageFeatures("0" * 16, "0" * 16, b), ImageFeatures("f" * 16, "f" * 16, a))
    assert result.clip_cosine is not None and "CLIP similarity" in result.evidence


def test_health_shows_clip_status_with_an_injected_model(tmp_path: Path) -> None:
    clip = ClipEmbedder(True, model=FakeClip())
    with TestClient(create_app(make_settings(tmp_path, enable_clip=True), clip=clip)) as client:
        assert client.get("/health").json()["engine"]["clip"] == "injected"
        body = client.post("/api/v1/check", json={"handle": "nairobi_sneakervault_official_ke"}).json()
        assert "CLIP similarity" in body["dimensions"][0]["evidence"]  # seeded with embeddings
