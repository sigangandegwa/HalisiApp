"""Identity (handle / name look-alike) and scam-language signals (TSK-016, docs/BACKEND.md 6.4 + 6.6).

Pure functions: strings in, scores out. No network, no DB.

MATCHER v2.1 (2026-09-27): Jaro-Winkler rewards a shared prefix, so every ``nairobi_*`` handle
scored high against ``nairobisneakervault`` (``nairobi_bakery`` 77.7, the real competitor
``nairobisneakerhub`` 88.4). v2.1 keeps the spec's three comparisons but:

* lowers the Jaro-Winkler weight (``JW_WEIGHT``), and
* compares the **distinctive remainder**: after removing the shared prefix and suffix, if both
  sides still differ by more than a typo (``TYPO_MAX_EDITS``), the pair score is pulled towards
  the similarity of those remainders. ``hub`` vs ``vault`` is a different brand; ``vualt`` vs
  ``vault`` is a typo.
* A target that is a strict truncation of the reference (``nairobi`` vs ``nairobisneakervault``)
  gets plain edit similarity, without the prefix bonus.
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from rapidfuzz import fuzz
from rapidfuzz.distance import OSA, JaroWinkler, Levenshtein

AFFIXES: frozenset[str] = frozenset(
    {
        "official",
        "real",
        "original",
        "genuine",
        "the",
        "ke",
        "kenya",
        "254",
        "nairobi_official",
        "shop",
        "store",
        "online",
        "deals",
        "offers",
        "hq",
        "team",
        "care",
        "support",
    }
)
HOMOGLYPHS: tuple[tuple[str, str], ...] = (
    ("rn", "m"),
    ("vv", "w"),
    ("0", "o"),
    ("1", "l"),
    ("i", "l"),
    ("|", "l"),
    ("3", "e"),
    ("5", "s"),
    ("@", "a"),
)

JW_WEIGHT = 0.3  # spec v2 used 0.5; lowered to damp the prefix bias
REMAINDER_WEIGHT = 0.65  # share of the pair score taken from the distinctive remainder
TYPO_MAX_EDITS = 2  # remainders within this OSA distance count as a typo, not a new word
CONTAINMENT_SCORE = 95.0
CONTAINMENT_MIN_LEN = 6

LANGUAGE_TOKENS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (
        40,
        (
            "pay before delivery",
            "lipa kwanza",
            "lipa kabla",
            "pochi la biashara",
            "send money to",
            "tuma pesa",
            "deposit required",
            "pay via m-pesa before",
        ),
    ),
    (
        25,
        (
            "payment with order",
            "no refunds",
            "non-refundable",
            "offer ends today",
            "leo tu",
            "whatsapp only",
            "dm for price",
            "limited stock",
        ),
    ),
    (10, ("strictly delivery", "no physical shop", "inbox to order", "delivery countrywide", "order now")),
)
_LANGUAGE_PATTERNS: tuple[tuple[int, str, re.Pattern[str]], ...] = tuple(
    (weight, phrase, re.compile(r"(?<![\w])" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?![\w])"))
    for weight, phrases in LANGUAGE_TOKENS
    for phrase in phrases
)

_SEPARATORS = re.compile(r"[._\-\s]")
_TOKEN_SPLIT = re.compile(r"[^a-z0-9@|]+")


class _Handle(Protocol):
    handle: str


class MerchantLike(Protocol):
    """Anything with official handles, a business name and aliases (e.g. ``scorer.MerchantProfile``)."""

    official_handles: Sequence[_Handle]
    business_name: str
    aliases: Sequence[str]


@dataclass(frozen=True, slots=True)
class IdentityResult:
    """Identity dimension: 0-100 look-alike score and a human-readable explanation."""

    score: float
    evidence: str


@dataclass(frozen=True, slots=True)
class LanguageResult:
    """Language dimension. ``score`` is None only when there is no text at all."""

    score: float | None
    evidence: str | None
    phrases: tuple[str, ...] = ()


# --- normalisation ------------------------------------------------------------------------------


def _clean(value: str) -> str:
    """NFKC, lowercase, strip '@' and trailing '/' and surrounding whitespace."""
    return unicodedata.normalize("NFKC", value or "").strip().lower().lstrip("@").rstrip("/")


def normalize_handle(handle: str) -> str:
    """Lowercase, NFKC, strip '@' / trailing '/', and remove '.', '_', '-' and whitespace."""
    return _SEPARATORS.sub("", _clean(handle))


def fold_homoglyphs(value: str) -> str:
    """Replace look-alike characters (``rn``->``m``, ``0``->``o``, ``1``/``i``->``l``...) in order."""
    for old, new in HOMOGLYPHS:
        value = value.replace(old, new)
    return value


def tokens(value: str) -> list[str]:
    """Split a raw handle or name into lowercase tokens on separators."""
    return [t for t in _TOKEN_SPLIT.split(_clean(value)) if t]


def strip_affixes(parts: Iterable[str]) -> list[str]:
    """Drop scam affixes (``official``, ``ke``, ``shop``...) from a token list."""
    return [t for t in parts if t not in AFFIXES]


# --- pair similarity ----------------------------------------------------------------------------


def _common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        n += 1
    return n


def distinctive_similarity(target: str, reference: str) -> float:
    """0-100 similarity of two folded strings that discounts a shared, non-distinctive prefix/suffix.

    * identical -> 100
    * one side is the other plus/minus a block (truncation or insertion) -> plain edit ratio
    * remainders differ by at most ``TYPO_MAX_EDITS`` (typo) -> blended JW + edit ratio
    * otherwise -> pulled towards the Levenshtein similarity of the differing remainders
    """
    if not target or not reference:
        return 0.0
    if target == reference:
        return 100.0
    ratio = fuzz.ratio(target, reference)
    base = JW_WEIGHT * JaroWinkler.similarity(target, reference) * 100 + (1 - JW_WEIGHT) * ratio

    p = _common_prefix(target, reference)
    s = _common_prefix(target[p:][::-1], reference[p:][::-1])
    rem_t, rem_r = target[p : len(target) - s], reference[p : len(reference) - s]
    if not rem_t or not rem_r:
        return ratio
    if OSA.distance(rem_t, rem_r) <= TYPO_MAX_EDITS:
        return base
    remainder = Levenshtein.normalized_similarity(rem_t, rem_r) * 100
    return min(base, (1 - REMAINDER_WEIGHT) * base + REMAINDER_WEIGHT * remainder)


def _compare(target_raw: str, reference_raw: str) -> tuple[float, str]:
    """Best of the three spec comparisons for one (target, reference) pair, with evidence."""
    t_norm, r_norm = normalize_handle(target_raw), normalize_handle(reference_raw)
    t_fold, r_fold = fold_homoglyphs(t_norm), fold_homoglyphs(r_norm)
    if not t_fold or not r_fold:
        return 0.0, ""

    t_tokens = tokens(target_raw)
    affixes = [t for t in t_tokens if t in AFFIXES]
    t_core_raw = "".join(strip_affixes(t_tokens))
    r_core_raw = "".join(strip_affixes(tokens(reference_raw))) or r_norm
    t_core, r_core = fold_homoglyphs(t_core_raw), fold_homoglyphs(r_core_raw)

    candidates: list[tuple[float, str]] = [(distinctive_similarity(t_fold, r_fold), "spelling")]
    if affixes and t_core:
        candidates.append((distinctive_similarity(t_core, r_core), "core"))
    if len(r_fold) >= CONTAINMENT_MIN_LEN and r_fold in t_fold and r_fold != t_fold:
        candidates.append((CONTAINMENT_SCORE, "contains"))
    score, how = max(candidates, key=lambda c: c[0])

    shown_t, shown_r = target_raw.strip().lstrip("@"), _clean(reference_raw)
    affix_note = " + affix " + " ".join(f"'{a}'" for a in affixes) if affixes else ""
    if how == "spelling" and score == 100.0:
        kind = "same letters, different separators" if t_norm == r_norm else "look-alike characters"
        evidence = f"'{shown_t}' imitates '{shown_r}' ({kind})"
    elif how == "core" and score == 100.0:
        glyphs = "" if t_core_raw == r_core_raw else " with look-alike characters"
        evidence = f"'{shown_t}' is '{shown_r}'{glyphs}{affix_note}"
    elif how == "contains":
        evidence = f"'{shown_t}' contains '{shown_r}'{affix_note}"
    else:
        evidence = f"'{shown_t}' resembles '{shown_r}' ({score:.0f}% similar)"
    return score, evidence


def identity_score(
    target_handle: str | None, target_name: str | None, merchant: MerchantLike
) -> IdentityResult:
    """Look-alike score of a page's handle / display name against a merchant.

    Maximum over every official handle, the business name and every alias of:
      a) distinctive similarity on fold(normalize(x)) (JW + edit ratio, remainder-aware)
      b) the same on affix-stripped tokens
      c) containment: 95 if fold(ref) is inside fold(target) and len(ref) >= 6
    """
    targets = [t for t in (target_handle, target_name) if t and t.strip()]
    refs: list[str] = [
        h.handle for h in getattr(merchant, "official_handles", ()) or () if getattr(h, "handle", "")
    ]
    if getattr(merchant, "business_name", ""):
        refs.append(merchant.business_name)
    refs.extend(a for a in getattr(merchant, "aliases", ()) or () if a)
    if not targets or not refs:
        return IdentityResult(0.0, "No match")

    best_score, best_evidence = 0.0, "No match"
    for target in targets:
        for ref in refs:
            score, evidence = _compare(target, ref)
            if score > best_score:
                best_score, best_evidence = score, evidence
    return IdentityResult(round(best_score, 2), best_evidence)


# --- language -----------------------------------------------------------------------------------


def language_score(text: str | None) -> LanguageResult:
    """Weighted scam-phrase score (EN / SW / Sheng) with whole-word matching.

    Returns ``score=None`` when there is no text, ``0.0`` when there is text but no phrase matched,
    else ``min(100, sum of matched weights)``. Phrases must match on word boundaries, so "leo tu"
    does not fire inside "Leo tunauza".
    """
    if not text or not text.strip():
        return LanguageResult(None, None)
    lowered = text.lower()
    total = 0
    matched: list[str] = []
    for weight, phrase, pattern in _LANGUAGE_PATTERNS:
        if pattern.search(lowered):
            total += weight
            matched.append(phrase)
    if not matched:
        return LanguageResult(0.0, "No scam phrases found")
    return LanguageResult(min(100.0, float(total)), ", ".join(f"'{p}'" for p in matched), tuple(matched))
