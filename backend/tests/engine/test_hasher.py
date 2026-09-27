"""Tests for app.engine.hasher (TSK-015). Replaces the network-dependent root test_hash.py."""

import itertools

import pytest

from app.engine.hasher import (
    ImageFeatures,
    clip_similarity,
    compute_hashes,
    cosine,
    hamming,
    hash_similarity,
    visual_score,
)
from app.engine.imaging import normalize
from tests.engine import imagegen as gen


def features(img, embedding=None) -> ImageFeatures:
    hashes = compute_hashes(normalize(img))
    return ImageFeatures(phash=hashes.phash, dhash=hashes.dhash, embedding=embedding)


# --- calibration curve ----------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("distance", "expected"), [(0, 100.0), (4, 100.0), (14, 50.0), (24, 0.0), (32, 0.0), (64, 0.0)]
)
def test_hash_similarity_curve(distance, expected):
    assert hash_similarity(distance) == expected


def test_unrelated_average_distance_scores_zero():
    """Regression for v1 (`100 - d/64*100`), which gave the typical unrelated distance of 32 a 50 % score."""
    assert hash_similarity(32) == 0.0


@pytest.mark.parametrize("distance", [-1, 65])
def test_hash_similarity_rejects_impossible_distances(distance):
    with pytest.raises(ValueError):
        hash_similarity(distance)


@pytest.mark.parametrize(
    ("cos", "expected"), [(1.0, 100.0), (0.93, 100.0), (0.865, 50.0), (0.80, 0.0), (0.2, 0.0)]
)
def test_clip_similarity_curve(cos, expected):
    assert clip_similarity(cos) == pytest.approx(expected, abs=0.01)


# --- primitives -----------------------------------------------------------------------------------

def test_compute_hashes_returns_64_bit_hex():
    hashes = compute_hashes(normalize(gen.sneaker_logo()))
    for value in (hashes.phash, hashes.dhash):
        assert len(value) == 16
        int(value, 16)


def test_hamming_counts_bits_and_accepts_uppercase():
    assert hamming("0000000000000000", "000000000000000f") == 4
    assert hamming("FFFFFFFFFFFFFFFF", "ffffffffffffffff") == 0
    assert hamming("0000000000000000", "ffffffffffffffff") == 64


@pytest.mark.parametrize("bad", ["", "abc", "zzzzzzzzzzzzzzzz", "0" * 17, None])
def test_hamming_rejects_malformed_hashes(bad):
    with pytest.raises(ValueError):
        hamming(bad, "0" * 16)


def test_cosine():
    assert cosine([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine([0.0, 0.0], [1.0, 0.0]) == 0.0
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 0.0])


# --- clone detection on generated logos ------------------------------------------------------------

@pytest.mark.parametrize("name", list(gen.ALL_LOGOS))
def test_identical_logo_scores_100(name):
    logo = gen.ALL_LOGOS[name]()
    result = visual_score(features(logo), features(logo))
    assert result.score == 100.0
    assert result.phash_distance == 0
    assert result.signal == "phash"


@pytest.mark.parametrize("name", list(gen.ALL_LOGOS))
@pytest.mark.parametrize("edit", [gen.jpeg, gen.downscale, gen.overlay_text, gen.recolor])
def test_copied_logo_survives_common_clone_edits(name, edit):
    logo = gen.ALL_LOGOS[name]()
    assert visual_score(features(edit(logo)), features(logo)).score >= 80


@pytest.mark.xfail(
    strict=True, reason="Known hash limit: 85% crops move pHash 10-28 bits. CLIP covers crops (TSK-017)."
)
@pytest.mark.parametrize("name", list(gen.ALL_LOGOS))
def test_cropped_logo_is_not_caught_by_hashes_alone(name):
    logo = gen.ALL_LOGOS[name]()
    assert visual_score(features(gen.crop(logo)), features(logo)).score >= 80


@pytest.mark.parametrize(("a", "b"), list(itertools.combinations(gen.ALL_LOGOS, 2)))
def test_unrelated_logos_score_at_most_10(a, b):
    result = visual_score(features(gen.ALL_LOGOS[a]()), features(gen.ALL_LOGOS[b]()))
    assert result.score <= 10, result.evidence


@pytest.mark.parametrize(("a", "b"), list(itertools.combinations(gen.ALL_LOGOS, 2)))
def test_edited_clone_of_one_logo_does_not_match_another(a, b):
    clone = gen.overlay_text(gen.jpeg(gen.ALL_LOGOS[a]()))
    assert visual_score(features(clone), features(gen.ALL_LOGOS[b]())).score <= 10


# --- CLIP combination -------------------------------------------------------------------------------

def test_clip_rescues_a_match_the_hashes_miss():
    """Hashes differ completely, but embeddings agree (e.g. a recoloured redraw): CLIP wins."""
    target = ImageFeatures(phash="0" * 16, dhash="0" * 16, embedding=[1.0, 0.0])
    reference = ImageFeatures(phash="f" * 16, dhash="f" * 16, embedding=[1.0, 0.0])
    result = visual_score(target, reference)
    assert result.signal == "clip"
    assert result.score == 100.0
    assert result.clip_cosine == pytest.approx(1.0)
    assert "CLIP similarity 1.00" in result.evidence


def test_ties_prefer_phash_and_evidence_lists_every_signal():
    logo = gen.sneaker_logo()
    result = visual_score(features(logo, [0.6, 0.8]), features(logo, [0.6, 0.8]))
    assert result.signal == "phash"
    assert result.evidence == "pHash distance 0/64 · dHash distance 0/64 · CLIP similarity 1.00"


def test_missing_embedding_on_either_side_skips_clip():
    logo = gen.sneaker_logo()
    result = visual_score(features(logo, [1.0, 0.0]), features(logo))
    assert result.clip_cosine is None
    assert "CLIP" not in result.evidence
