"""Look-alike handle generator for the typosquat watchlist (TSK-047, docs/PRODUCT_V2.md section 6).

Pure function: strings in, a ranked list of *plausible* impersonator handles out. It does not fetch
anything and does not claim any of the results exist; the watchlist service probes them separately.

The variants mirror what scammers actually register (and what ``matcher.py`` is built to catch):
look-alike characters (``vault`` -> ``vau1t``), separator changes, and "official"-style affixes.
"""

import re

# Single-character swaps scammers use. Keys are what appears in the real handle.
LOOKALIKES: dict[str, tuple[str, ...]] = {
    "l": ("1", "i"),
    "i": ("1", "l"),
    "o": ("0",),
    "e": ("3",),
    "s": ("5",),
    "m": ("rn",),
    "w": ("vv",),
    "u": ("v",),
    "v": ("u",),
}
SUFFIXES: tuple[str, ...] = (
    "_official",
    "official",
    "_official_ke",
    "_ke",
    "ke",
    "_kenya",
    "_shop",
    "_store",
    "_real",
    "_original",
    "254",
    "_",
)
PREFIXES: tuple[str, ...] = ("official_", "real_", "the")
HANDLE_RE = re.compile(r"^[a-z0-9._]{1,60}$")
DEFAULT_LIMIT = 80


def _name_tokens(business_name: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", business_name.lower()) if t]


def _joins(tokens: list[str]) -> list[str]:
    """Ways to write a multi-word name as a handle: ``a_b_c``, ``a.b.c``, ``abc`` and mixed splits."""
    if len(tokens) < 2:
        return []
    out = ["_".join(tokens), ".".join(tokens), "".join(tokens)]
    if len(tokens) == 3:
        a, b, c = tokens
        out += [f"{a}_{b}{c}", f"{a}{b}_{c}", f"{a}.{b}{c}", f"{a}{b}.{c}"]
    elif len(tokens) > 3:
        out += [f"{tokens[0]}_{''.join(tokens[1:])}", f"{''.join(tokens[:-1])}_{tokens[-1]}"]
    return out


def _homoglyphs(handle: str) -> list[str]:
    """One look-alike substitution at a time, left to right (so the most visible swaps come first)."""
    out: list[str] = []
    for index, char in enumerate(handle):
        for swap in LOOKALIKES.get(char, ()):
            out.append(handle[:index] + swap + handle[index + 1 :])
    return out


def _transpositions(handle: str) -> list[str]:
    """Adjacent-letter swaps (``vualt``): common typo-squats."""
    out = []
    for index in range(len(handle) - 1):
        if handle[index] != handle[index + 1] and handle[index].isalpha() and handle[index + 1].isalpha():
            out.append(handle[:index] + handle[index + 1] + handle[index] + handle[index + 2 :])
    return out


def handle_variants(handle: str, business_name: str = "", *, limit: int = DEFAULT_LIMIT) -> list[str]:
    """Plausible look-alike handles for ``handle`` (never including ``handle`` itself), most likely first.

    Order: look-alike characters, separator/name forms with affixes, affixes on the real handle,
    prefixes, then typo transpositions. Only syntactically valid handles are returned, de-duplicated.
    """
    real = handle.strip().lower().lstrip("@")
    if not HANDLE_RE.match(real):
        return []
    bases = [real, *_joins(_name_tokens(business_name))]
    bases = list(dict.fromkeys(b for b in bases if b))

    ranked: list[str] = []
    ranked += _homoglyphs(real)
    ranked += [b for b in bases[1:]]                       # same name, different separators
    for base in bases:
        ranked += [base + s for s in SUFFIXES]
    for base in bases:
        ranked += [p + base for p in PREFIXES]
    for base in bases[1:]:
        ranked += _homoglyphs(base)[:6]
    ranked += _transpositions(real)

    seen = {real}
    out: list[str] = []
    for candidate in ranked:
        if candidate in seen or not HANDLE_RE.match(candidate):
            continue
        seen.add(candidate)
        out.append(candidate)
        if len(out) >= limit:
            break
    return out
