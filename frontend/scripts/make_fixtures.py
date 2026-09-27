"""Generate the frontend's hand-authored demo fixtures (frontend/src/lib/fixtures/*.json).

Why a script: fixture numbers must be internally consistent (composite = renormalised weighted sum,
Hamming distance = popcount(a ^ b), overrides applied). Rather than typing numbers by hand, this
script draws fictional logos with PIL and runs the backend's *own* engine on them, read-only:

    backend/.venv/Scripts/python.exe frontend/scripts/make_fixtures.py      (Windows)
    backend/.venv/bin/python frontend/scripts/make_fixtures.py              (macOS / Linux)

It imports `app.engine.*` and `app.ingestion.extractors` from backend/ but never writes there.
Outputs:
    frontend/public/fixtures/logos/*.png|jpg     logos and clone avatars
    frontend/src/lib/fixtures/*.json             contract-shaped fixtures (BACKEND.md section 5)

These are PLACEHOLDERS until the backend seeder (TSK-007) writes engine+DB fixtures into
frontend/src/lib/fixtures/seed/, which the loader prefers. All businesses are fictional.
"""

from __future__ import annotations

import gzip
import io
import json
import statistics
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from PIL import Image, ImageDraw, ImageFont, ImageOps  # noqa: E402

from app.engine import hasher, imaging  # noqa: E402
from app.engine.hasher import ImageFeatures  # noqa: E402
from app.engine.payment import canonical_phone, canonical_till, mask_phone  # noqa: E402
from app.engine.scorer import (  # noqa: E402
    MerchantProfile,
    OfficialHandle,
    ScoringContext,
    TargetProfile,
    safe_action,
    score_against_all,
)
from app.ingestion.extractors import extract_payment_evidence  # noqa: E402

OUT_JSON = ROOT / "frontend" / "src" / "lib" / "fixtures"
OUT_IMG = ROOT / "frontend" / "public" / "fixtures" / "logos"
PUBLIC_IMG = "/fixtures/logos"
NS = uuid.UUID("5f0c2f4e-4a1b-4f7e-9a51-6d0b8c7e2a10")
TODAY = date(2026, 9, 27)
FONTS = Path("C:/Windows/Fonts")
SIZE = 400
SS = 2  # supersampling factor for smooth edges


def uid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "|".join(parts)))


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in (FONTS / name, Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size * SS)
    return ImageFont.load_default()


# --- logo drawing (fictional brands) ------------------------------------------------------------

def canvas(bg: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (SIZE * SS, SIZE * SS), bg)
    return img, ImageDraw.Draw(img)


def centered(d: ImageDraw.ImageDraw, y: int, text: str, fnt, fill: str, tracking: int = 0) -> None:
    if tracking:
        widths = [d.textlength(ch, font=fnt) for ch in text]
        total = sum(widths) + tracking * SS * (len(text) - 1)
        x = (SIZE * SS - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, y * SS), ch, font=fnt, fill=fill)
            x += w + tracking * SS
        return
    w = d.textlength(text, font=fnt)
    d.text(((SIZE * SS - w) / 2, y * SS), text, font=fnt, fill=fill)


def finish(img: Image.Image) -> Image.Image:
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def logo_nsv(bg: str = "#1F2A44", ink: str = "#EFE6D2") -> Image.Image:
    import math

    img, d = canvas(bg)
    c, r = SIZE * SS / 2, 150 * SS
    d.ellipse((c - r, c - r, c + r, c + r), outline=ink, width=9 * SS)
    for i in range(36):
        a = math.tau * i / 36
        r1, r2 = (r - 20 * SS, r - 6 * SS) if i % 3 else (r - 34 * SS, r - 6 * SS)
        d.line((c + r1 * math.cos(a), c + r1 * math.sin(a), c + r2 * math.cos(a), c + r2 * math.sin(a)),
               fill=ink, width=4 * SS)
    centered(d, 128, "NSV", font("georgiab.ttf", 104), ink)
    centered(d, 252, "SNEAKER VAULT", font("arialbd.ttf", 19), ink, tracking=4)
    return finish(img)


def logo_kg(bg: str = "#EBCFC2", sun: str = "#B8583F", ink: str = "#5A2A1E") -> Image.Image:
    img, d = canvas(bg)
    c = SIZE * SS / 2
    r = 92 * SS
    cy = 150 * SS
    d.ellipse((c - r, cy - r, c + r, cy + r), fill=sun)
    for i, h in enumerate((6, 9, 12, 15)):
        y = cy + (14 + i * 22) * SS
        d.rectangle((c - r - 4, y, c + r + 4, y + h * SS // 2), fill=bg)
    centered(d, 268, "kilimani glow", font("georgiai.ttf", 44), ink)
    return finish(img)


def logo_pt(bg: str = "#0F5563", sand: str = "#E9D8AE") -> Image.Image:
    import math

    img, d = canvas(bg)
    centered(d, 70, "PT", font("georgiab.ttf", 132), sand)
    for row in range(4):
        pts = []
        y0 = (248 + row * 22) * SS
        for x in range(0, SIZE * SS + 1, 8):
            pts.append((x, y0 + 9 * SS * math.sin(x / (26 * SS) + row)))
        d.line(pts, fill=sand, width=5 * SS)
    centered(d, 350, "PWANI THREADS", font("arialbd.ttf", 18), sand, tracking=4)
    return finish(img)


def logo_hub() -> Image.Image:
    img, d = canvas("#E07A2E")
    c = SIZE * SS / 2
    import math

    r = 140 * SS
    hexagon = [(c + r * math.cos(math.pi / 6 + i * math.pi / 3), c + r * math.sin(math.pi / 6 + i * math.pi / 3))
               for i in range(6)]
    d.polygon(hexagon, outline="#FFF6EA", width=10 * SS)
    centered(d, 150, "HUB", font("arialbd.ttf", 92), "#FFF6EA")
    centered(d, 262, "NAIROBI SNEAKERS", font("arialbd.ttf", 16), "#FFF6EA", tracking=3)
    return finish(img)


def logo_kb() -> Image.Image:
    img, d = canvas("#F4F0E8")
    c = SIZE * SS / 2
    r = 132 * SS
    d.ellipse((c - r, c - r, c + r, c + r), outline="#1B1B1B", width=5 * SS)
    centered(d, 130, "KB", font("timesbd.ttf", 110), "#1B1B1B")
    centered(d, 262, "BEAUTY BAR", font("arialbd.ttf", 16), "#1B1B1B", tracking=5)
    return finish(img)


def logo_mfh() -> Image.Image:
    img, d = canvas("#5E2A55")
    d.rectangle((60 * SS, 60 * SS, 340 * SS, 340 * SS), outline="#D9B45A", width=6 * SS)
    centered(d, 128, "MFH", font("timesbd.ttf", 104), "#D9B45A")
    centered(d, 250, "MOMBASA", font("arialbd.ttf", 18), "#D9B45A", tracking=6)
    return finish(img)


# --- avatar variants (how clones re-use a logo) --------------------------------------------------

def v_jpeg(img: Image.Image, q: int = 35) -> Image.Image:
    buf = io.BytesIO()
    img.resize((320, 320), Image.LANCZOS).save(buf, "JPEG", quality=q)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def v_crop(img: Image.Image, keep: float = 0.85) -> Image.Image:
    w = int(SIZE * keep)
    o = (SIZE - w) // 2
    return img.crop((o, o, o + w, o + w)).resize((SIZE, SIZE), Image.LANCZOS)


def v_recolor(img: Image.Image) -> Image.Image:
    # hue rotation by channel swap: keeps the shapes, changes the brand colour
    r, g, b = img.split()
    return Image.merge("RGB", (b, r, g))


def v_overlay(img: Image.Image, text: str) -> Image.Image:
    small = img.resize((96, 96), Image.LANCZOS).resize((SIZE, SIZE), Image.BICUBIC)
    d = ImageDraw.Draw(small)
    d.rectangle((0, 318, SIZE, 370), fill="#C8102E")
    fnt = ImageFont.truetype(str(FONTS / "arialbd.ttf"), 30) if (FONTS / "arialbd.ttf").exists() else None
    w = d.textlength(text, font=fnt)
    d.text(((SIZE - w) / 2, 326), text, font=fnt, fill="#FFFFFF")
    return small


def save(img: Image.Image, name: str) -> tuple[str, ImageFeatures]:
    """Save an avatar/logo and return (public url, engine features computed from the saved bytes)."""
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    ext = "jpg" if name.endswith("_jpeg") or name.endswith("_clone") else "webp"
    path = OUT_IMG / f"{name}.{ext}"
    if ext == "jpg":
        img.save(path, "JPEG", quality=35)          # clones re-save the logo as a low-quality JPEG
    else:
        img.save(path, "WEBP", quality=86, method=6)
    data = path.read_bytes()
    hashes = hasher.compute_hashes(imaging.normalize_image(data))
    return f"{PUBLIC_IMG}/{path.name}", ImageFeatures(phash=hashes.phash, dhash=hashes.dhash)


# --- merchants (fictional) -----------------------------------------------------------------------

@dataclass
class Merchant:
    profile: MerchantProfile
    logo_url: str
    logo: Image.Image
    category: str
    location: str
    verified_since: str
    handle_urls: dict[str, str]


def official_url(platform: str, handle: str) -> str:
    return {
        "instagram": f"https://instagram.com/{handle}",
        "facebook": f"https://facebook.com/{handle}",
        "tiktok": f"https://tiktok.com/@{handle}",
    }[platform]


def make_merchant(slug, name, logo, handles, mpesa_type, mpesa_number, account, phones, est, cat, loc, since):
    url, feats = save(logo, slug)
    profile = MerchantProfile(
        id=uid("merchant", slug),
        business_name=name,
        slug=slug,
        official_handles=tuple(OfficialHandle(p, h) for p, h in handles),
        aliases=(),
        logo=feats,
        phone_numbers=tuple(phones),
        mpesa_type=mpesa_type,
        mpesa_number=mpesa_number,
        mpesa_account_name=account,
        established_on=est,
    )
    return Merchant(profile, url, logo, cat, loc, since, {h: official_url(p, h) for p, h in handles})


MERCHANTS = [
    make_merchant("nairobi-sneaker-vault", "Nairobi Sneaker Vault", logo_nsv(),
                  [("instagram", "nairobisneakervault"), ("tiktok", "nairobisneakervault")],
                  "till", "543210", "NAIROBI SNEAKER VAULT", ["+254700000111"], date(2019, 3, 1),
                  "Sneakers & streetwear", "Nairobi CBD", "2026-09-01"),
    make_merchant("kilimani-glow", "Kilimani Glow", logo_kg(),
                  [("instagram", "kilimaniglow"), ("facebook", "kilimaniglow")],
                  "paybill", "606060", "KILIMANI GLOW", ["+254700000222"], date(2021, 6, 15),
                  "Beauty & skincare", "Kilimani, Nairobi", "2026-09-03"),
    make_merchant("pwani-threads", "Pwani Threads", logo_pt(),
                  [("instagram", "pwanithreads"), ("facebook", "pwanithreads")],
                  "pochi", "+254700000333", "PWANI THREADS", ["+254700000333"], date(2020, 11, 2),
                  "Coastal fashion", "Mombasa", "2026-09-05"),
]
BY_SLUG = {m.profile.slug: m for m in MERCHANTS}
PROFILES = [m.profile for m in MERCHANTS]

# Numbers taken from confirmed community reports (BACKEND.md section 7.3: 2 confirmed of 5).
REPORTS = [
    ("+254798999111", "confirmed"), ("+254798999111", "pending"), ("+254798999111", "pending"),
    ("+254798999222", "confirmed"), ("+254798999222", "pending"),
]
CONFIRMED = frozenset(n for n, s in REPORTS if s == "confirmed")
CTX = ScoringContext(today=TODAY, confirmed_reported=CONFIRMED)


# --- targets -------------------------------------------------------------------------------------

@dataclass
class Target:
    key: str
    merchant: str               # slug of the merchant the scenario is about
    kind: str                   # blatant | subtle | competitor | suspicious | official
    handle: str
    display_name: str
    bio: str
    avatar: Image.Image | None
    avatar_name: str
    followers: int | None
    posts: int | None
    created: date | None
    status: str = "detected"
    first_seen: str = "2026-09-27T08:00:00Z"
    history: tuple[tuple[str, str], ...] = ()
    read_at: str | None = None


nsv, kg, pt = (BY_SLUG[s] for s in ("nairobi-sneaker-vault", "kilimani-glow", "pwani-threads"))

TARGETS = [
    Target("nsv-blatant", nsv.profile.slug, "blatant", "nairobi_sneakervault_official_ke",
           "Nairobi Sneaker Vault Official",
           "Original sneakers, Nairobi. Lipa kwanza, pay before delivery. Order on WhatsApp 0798 999 111. "
           "Offer ends today!",
           v_jpeg(nsv.logo), "nsv_clone", 212, 9, date(2026, 9, 19),
           first_seen="2026-09-27T11:48:05Z"),
    Target("nsv-subtle", nsv.profile.slug, "subtle", "nairobisneakervau1t", "Nairobi Sneaker Vault",
           "Sneakers countrywide. Tuma pesa kwa Pochi la Biashara 0798 999 444 then DM for price.",
           v_crop(v_recolor(nsv.logo)), "nsv_subtle", 530, 14, None,
           status="advisory_sent", first_seen="2026-09-26T16:20:41Z",
           history=(("advisory_sent", "2026-09-26T17:02:10Z"),), read_at="2026-09-26T16:31:00Z"),
    Target("nsv-competitor", nsv.profile.slug, "competitor", "nairobisneakerhub", "Nairobi Sneaker Hub",
           "Sneakers & streetwear in Nairobi. Buy Goods Till 778812. Delivery countrywide.",
           logo_hub(), "nairobisneakerhub", 4820, 312, None),
    Target("nsv-suspicious", nsv.profile.slug, "suspicious", "sneakervault_resale_ke", "Sneaker Vault Resale KE",
           "Pre-owned and new kicks. Viewing by appointment in Nairobi.",
           v_overlay(nsv.logo, "RESALE"), "sneakervault_resale_ke", 1340, 41, None,
           first_seen="2026-09-27T09:05:12Z"),
    Target("nsv-official", nsv.profile.slug, "official", "nairobisneakervault", "Nairobi Sneaker Vault",
           "", nsv.logo, "nairobi-sneaker-vault", None, None, None),

    Target("kg-blatant", kg.profile.slug, "blatant", "kilimaniglow_official_ke", "Kilimani Glow Official",
           "Skincare deals. Payment with order only, send to 0798 999 222. No refunds.",
           v_jpeg(kg.logo), "kg_clone", 96, 6, date(2026, 9, 22),
           status="takedown_filed", first_seen="2026-09-25T10:14:33Z",
           history=(("advisory_sent", "2026-09-25T10:40:00Z"), ("takedown_filed", "2026-09-25T11:05:00Z")),
           read_at="2026-09-25T10:20:00Z"),
    Target("kg-subtle", kg.profile.slug, "subtle", "kilimanigl0w", "Kilimani Glow",
           "Glow kits in stock. Pochi la Biashara 0798 999 555. Leo tu!",
           v_crop(v_recolor(kg.logo)), "kg_subtle", 410, 11, None, first_seen="2026-09-27T07:31:50Z"),
    Target("kg-competitor", kg.profile.slug, "competitor", "kilimanibeauty", "Kilimani Beauty Bar",
           "Salon and skincare in Kilimani. Paybill 303909. Walk-ins welcome.",
           logo_kb(), "kilimanibeauty", 2210, 188, None),
    Target("kg-official", kg.profile.slug, "official", "kilimaniglow", "Kilimani Glow",
           "", kg.logo, "kilimani-glow", None, None, None),

    Target("pt-blatant", pt.profile.slug, "blatant", "pwanithreads_official_ke", "Pwani Threads Official",
           "Kitenge and coastal wear. Deposit required, send to 0798 999 333. Limited stock.",
           v_jpeg(pt.logo), "pt_clone", 150, 7, date(2026, 9, 20),
           status="resolved", first_seen="2026-09-21T13:02:00Z",
           history=(("advisory_sent", "2026-09-21T13:30:00Z"), ("takedown_filed", "2026-09-21T14:10:00Z"),
                    ("resolved", "2026-09-23T09:00:00Z")),
           read_at="2026-09-21T13:10:00Z"),
    Target("pt-subtle", pt.profile.slug, "subtle", "pwanlthreads", "Pwani Threads",
           "New drops every Friday. Tuma pesa 0798 999 666 kupata order yako.",
           v_crop(v_recolor(pt.logo)), "pt_subtle", 380, 12, None, first_seen="2026-09-27T06:12:09Z"),
    Target("pt-competitor", pt.profile.slug, "competitor", "mombasa_fashion_house", "Mombasa Fashion House",
           "Tailoring and ready-to-wear in Nyali. Till 441207.",
           logo_mfh(), "mombasa_fashion_house", 3900, 260, None),
    Target("pt-official", pt.profile.slug, "official", "pwanithreads", "Pwani Threads",
           "", pt.logo, "pwani-threads", None, None, None),
]


# --- serialisation into the BACKEND.md section 5 shapes -------------------------------------------

def public_payment(m: MerchantProfile) -> dict:
    return {"type": m.mpesa_type, "number": m.mpesa_number, "account_name": m.mpesa_account_name}


def matched(m: MerchantProfile) -> dict:
    mm = next(x for x in MERCHANTS if x.profile.id == m.id)
    return {
        "id": m.id,
        "business_name": m.business_name,
        "slug": m.slug,
        "logo_url": mm.logo_url,
        "official_handles": [
            {"platform": h.platform, "handle": h.handle, "url": official_url(h.platform, h.handle)}
            for h in m.official_handles
        ],
        "payment": public_payment(m),
    }


def public_profile(mm: Merchant) -> dict:
    m = mm.profile
    return {
        "id": m.id,
        "business_name": m.business_name,
        "slug": m.slug,
        "logo_url": mm.logo_url,
        "category": mm.category,
        "location": mm.location,
        "established_on": m.established_on.isoformat() if m.established_on else None,
        "is_verified": True,
        "official_handles": matched(m)["official_handles"],
        "payment": public_payment(m),
        "verified_since": mm.verified_since,
    }


def score(t: TargetProfile):
    start = time.perf_counter()
    result = score_against_all(t, PROFILES, CTX)
    elapsed = max(1, round((time.perf_counter() - start) * 1000))
    return result, elapsed


def check_result(scan_id: str, target_json: dict, t: TargetProfile, result, elapsed: int, threat_id):
    m = result.merchant
    visual = result.visual
    hashes = None
    if visual is not None and t.avatar is not None:
        ref = m.logo if m is not None else min(
            (p.logo for p in PROFILES if p.logo), key=lambda f: hasher.hamming(f.phash, t.avatar.phash))
        hashes = {"target_phash": t.avatar.phash, "reference_phash": ref.phash,
                  "hamming_distance": hasher.hamming(t.avatar.phash, ref.phash)}
    safe = None
    if m is not None:
        en, sw = safe_action(m, t.platform)
        safe = {"text": en, "text_sw": sw}
    return {
        "scan_id": scan_id,
        "verdict": result.verdict,
        "score": round(result.score, 2),
        "confidence": result.confidence,
        "target": target_json,
        "matched_merchant": matched(m) if m is not None else None,
        "dimensions": [] if result.verdict == "official" else result.dimensions_payload(),
        "reasons": result.reasons_payload(),
        "hashes": None if result.verdict == "official" else hashes,
        "safe_action": safe,
        "threat_id": threat_id,
        "elapsed_ms": elapsed,
    }


def target_profile(handle, display_name, bio, avatar_feats, followers, posts, created) -> TargetProfile:
    return TargetProfile(
        platform="instagram", handle=handle, display_name=display_name, bio=bio or None,
        avatar=avatar_feats, payment=extract_payment_evidence(bio),
        follower_count=followers, post_count=posts, account_created_on=created,
    )


def target_json(handle, display_name, avatar_url, followers, posts, created) -> dict:
    return {
        "platform": "instagram",
        "handle": handle,
        "display_name": display_name,
        "url": f"https://instagram.com/{handle}",
        "avatar_url": avatar_url,
        "follower_count": followers,
        "post_count": posts,
        "account_created_on": created.isoformat() if created else None,
        "fetched_via": "seed",
    }


def fmt_phone(e164: str) -> str:
    local = "0" + e164[4:]
    return f"{local[:4]} {local[4:7]} {local[7:]}"


def pay_line(m: MerchantProfile) -> str:
    acct = f" ({m.mpesa_account_name})" if m.mpesa_account_name else ""
    if m.mpesa_type == "till":
        return f"Buy Goods Till {m.mpesa_number}{acct}"
    if m.mpesa_type == "paybill":
        return f"Paybill {m.mpesa_number}{acct}"
    return f"Pochi la Biashara {fmt_phone(m.mpesa_number)}{acct}"


def pay_line_sw(m: MerchantProfile) -> str:
    acct = f" ({m.mpesa_account_name})" if m.mpesa_account_name else ""
    if m.mpesa_type == "till":
        return f"Till {m.mpesa_number}{acct}"
    if m.mpesa_type == "paybill":
        return f"Paybill {m.mpesa_number}{acct}"
    return f"Pochi la Biashara {fmt_phone(m.mpesa_number)}{acct}"


def playbooks(detail: dict, lang: str) -> dict:
    """Deterministic template playbooks built only from facts in the threat detail."""
    m = next(x.profile for x in MERCHANTS if x.profile.id == detail["matched_merchant"]["id"])
    real = next((h.handle for h in m.official_handles if h.platform == "instagram"), m.official_handles[0].handle)
    fake = detail["target"]["handle"]
    phones = [fmt_phone(p) for p in detail["extracted_phones"]]
    dims = {d["key"]: d for d in detail["dimensions"]}
    first_seen = detail["first_seen_at"][:10]
    dist = detail["hashes"]["hamming_distance"] if detail.get("hashes") else None
    money = f" Don't send money to {', '.join(phones)}." if phones else ""
    money_sw = f" Usitume pesa kwa {', '.join(phones)}." if phones else ""

    if lang == "sw":
        title = f"Tahadhari: ukurasa feki wa {m.business_name}"
        body = (f"Tahadhari kwa wateja wetu: @{fake} si {m.business_name}. Ukurasa huo unatumia jina letu "
                f"na nembo yetu bila ruhusa.{money_sw} Ukurasa wetu rasmi ni @{real} pekee. "
                f"Lipa tu kupitia {pay_line_sw(m)}. Kama tayari umetuma pesa, piga ripoti kwa Safaricom "
                f"na utujulishe kupitia ukurasa wetu rasmi.")
    else:
        title = f"Scam alert: fake {m.business_name} page"
        body = (f"Heads up: @{fake} is not {m.business_name}. It uses our name and logo without "
                f"permission.{money} Our only official page is @{real}. Pay only via {pay_line(m)}. "
                f"If you have already paid the fake page, report it to Safaricom and let us know through "
                f"our official page.")

    evidence = []
    if dist is not None:
        evidence.append(f"its profile picture is a copy of our logo (perceptual-hash distance {dist}/64)")
    for key, label in (("identity", "name and handle"), ("payment", "payment details")):
        d = dims.get(key)
        if d and d["available"]:
            evidence.append(f"{label} score {d['score']:.0f}/100")
    takedown = (
        f"I am the owner of {m.business_name}, whose official Instagram account is @{real}. "
        f"The account @{fake} ({detail['target']['url']}) is impersonating my business: it uses our business "
        f"name, {'; '.join(evidence)}. "
        + (f"It asks our customers to send payment to {', '.join(phones)}, which is not our number. "
           if phones else "")
        + f"Halisi first recorded this account on {first_seen}, with an impersonation score of "
        f"{detail['score']:.0f}/100. Please remove the account."
    )
    report_numbers = ", ".join(phones) if phones else "(no payment number recorded)"
    safaricom = (
        f"To the Safaricom fraud team,\n\nThe number {report_numbers} is being used to collect payments from "
        f"customers of {m.business_name} through a fake Instagram page, @{fake} ({detail['target']['url']}). "
        f"{m.business_name} is paid only via {pay_line(m)}. We first recorded the fake page on {first_seen}. "
        f"Please investigate the number above.\n\n{m.business_name}"
    )
    kecirt = (
        f"To the National KE-CIRT/CC,\n\nWe are reporting the impersonation of {m.business_name} on Instagram. "
        f"The account @{fake} ({detail['target']['url']}) copies our business name and logo and "
        + (f"directs customers to pay {', '.join(phones)}. " if phones else "targets our customers. ")
        + f"Our official account is @{real}. First recorded on {first_seen}. This may be an offence under "
        f"the Computer Misuse and Cybercrimes Act, 2018. Evidence (screenshots, hashes and scores) is "
        f"available on request.\n\n{m.business_name}"
    )
    return {
        "generator": "template",
        "model": None,
        "prompt_ids": [],
        "consumer_warning": {"title": title, "body": body,
                             "whatsapp_share_url": "https://wa.me/?text=" + quote(f"{title}\n\n{body}")},
        "platform_takedown": {"platform": "instagram",
                              "report_url": "https://help.instagram.com/contact/636276399721841",
                              "body": takedown},
        "safaricom_report": {"channel": "email", "to": "",
                             "subject": f"Fraud report: number used to impersonate {m.business_name}",
                             "body": safaricom},
        "kecirt_report": {"to": "", "subject": f"Incident report: impersonation of {m.business_name} on Instagram",
                          "body": kecirt},
    }


def main() -> None:
    OUT_JSON.mkdir(parents=True, exist_ok=True)
    checks, threats, alerts, lookups = [], [], [], {}
    elapsed_all = []

    for t in TARGETS:
        avatar_url, feats = save(t.avatar, t.avatar_name) if t.kind != "official" else (
            BY_SLUG[t.merchant].logo_url, BY_SLUG[t.merchant].profile.logo)
        tp = target_profile(t.handle, t.display_name, t.bio, feats, t.followers, t.posts, t.created)
        result, elapsed = score(tp)
        elapsed_all.append(elapsed)
        tid = uid("threat", t.key) if result.merchant is not None and result.score >= 70 else None  # BACKEND.md 5.11
        tj = target_json(t.handle, t.display_name, avatar_url, t.followers, t.posts, t.created)
        if t.kind == "official":
            tj.update(follower_count=None, post_count=None)
        cr = check_result(uid("scan", t.key), tj, tp, result, elapsed, tid)
        cr["_fixture"] = {"key": t.key, "kind": t.kind, "rules": list(result.rules)}
        checks.append(cr)
        print(f"{t.key:16} {result.verdict:14} {result.score:6.2f} conf {result.confidence:.2f} "
              f"rules {','.join(result.rules) or '-':8} hash {cr['hashes']['hamming_distance'] if cr['hashes'] else '-'}")

        if tid:
            phones = list(dict.fromkeys(p for p in map(canonical_phone, tp.payment.phones) if p))
            tills = list(dict.fromkeys(x for x in map(canonical_till, tp.payment.tills) if x))
            history = [{"status": "detected", "at": t.first_seen}] + [{"status": s, "at": a} for s, a in t.history]
            detail = {k: v for k, v in cr.items() if k != "_fixture"}
            detail.update(
                id=tid, merchant_id=result.merchant.id, status=t.status, first_seen_at=t.first_seen,
                status_history=history, extracted_phones=phones, extracted_tills=tills, playbooks_generated=[],
            )
            threats.append(detail)
            if result.verdict == "impersonation":
                summary = {
                    "id": tid, "platform": "instagram", "target_handle": t.handle, "target_url": tj["url"],
                    "avatar_url": avatar_url, "composite_score": cr["score"], "verdict": cr["verdict"],
                    "status": t.status, "first_seen_at": t.first_seen,
                    "top_reason": cr["reasons"][0] if cr["reasons"] else None,
                }
                created = (datetime.fromisoformat(t.first_seen.replace("Z", "+00:00")) + timedelta(seconds=4))
                alerts.append({
                    "id": uid("alert", t.key, "new"), "merchant_id": result.merchant.id, "threat_id": tid,
                    "kind": "new_threat", "title": f"Impersonator detected: @{t.handle}",
                    "body": cr["reasons"][0]["text"] if cr["reasons"] else "A page is imitating your business.",
                    "score": cr["score"], "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "read_at": t.read_at, "threat": summary,
                })
                if t.status == "resolved":
                    at = t.history[-1][1]
                    alerts.append({
                        "id": uid("alert", t.key, "resolved"), "merchant_id": result.merchant.id,
                        "threat_id": tid, "kind": "resolved", "title": f"Taken down: @{t.handle}",
                        "body": "The impersonating page is no longer available.", "score": cr["score"],
                        "created_at": at, "read_at": at, "threat": summary,
                    })
            for p in phones:
                lookups.setdefault(p, {"linked": set()})["linked"].add(tid)

    # payment lookups (BACKEND.md section 5.3)
    payments = []
    for mm in MERCHANTS:
        m = mm.profile
        kind = "phone" if m.mpesa_type == "pochi" else m.mpesa_type
        normalized = canonical_phone(m.mpesa_number) if kind == "phone" else m.mpesa_number
        payments.append({"kind": kind, "normalized": normalized,
                         "display": fmt_phone(normalized) if kind == "phone" else m.mpesa_number,
                         "status": "official", "merchant": public_profile(mm),
                         "report_count": 0, "linked_threats": 0})
        for p in m.phone_numbers:
            if p != normalized:
                payments.append({"kind": "phone", "normalized": p, "display": fmt_phone(p), "status": "official",
                                 "merchant": public_profile(mm), "report_count": 0, "linked_threats": 0})
    for phone, info in sorted(lookups.items()):
        reports = [s for n, s in REPORTS if n == phone]
        payments.append({"kind": "phone", "normalized": phone, "display": mask_phone(phone),
                         "status": "reported" if "confirmed" in reports else "unknown", "merchant": None,
                         "report_count": len(reports), "linked_threats": len(info["linked"])})

    # stats (BACKEND.md section 5.9): honest counts over this fixture dataset
    def stats_for(mid: str | None) -> dict:
        ts = [t for t in threats if mid is None or t["merchant_id"] == mid]
        cutoff = datetime(2026, 9, 27, tzinfo=timezone.utc) - timedelta(days=7)
        imp7 = [t for t in ts if t["verdict"] == "impersonation"
                and datetime.fromisoformat(t["first_seen_at"].replace("Z", "+00:00")) >= cutoff]
        base = {
            "pages_scanned": len(checks) if mid is None else sum(
                1 for c in checks if (c["matched_merchant"] or {}).get("id") == mid),
            "threats_detected": len(ts),
            "impersonations_blocked_7d": len(imp7),
            "merchants_protected": len(MERCHANTS) if mid is None else 1,
            "median_detection_ms": int(statistics.median(elapsed_all)),
            "top_platforms": [{"platform": "instagram", "count": len(ts)}],
        }
        if mid is not None:
            base.update(active_threats=sum(1 for t in ts if t["status"] not in ("resolved", "false_positive")),
                        resolved=sum(1 for t in ts if t["status"] == "resolved"),
                        customers_warned_estimate=None)
        return base

    stats = {"global": stats_for(None), "merchants": {m.profile.id: stats_for(m.profile.id) for m in MERCHANTS}}

    books = {t["id"]: {"en": playbooks(t, "en"), "sw": playbooks(t, "sw")} for t in threats}

    # simulator: every tweak combination per merchant, scored by the real engine (BACKEND.md 5.10)
    sim = {}
    variants = {}
    for mm in MERCHANTS:
        base = mm.slug if hasattr(mm, "slug") else mm.profile.slug
        variants[mm.profile.id] = {
            "exact": (mm.logo_url, mm.profile.logo),
            "recolor": save(v_recolor(mm.logo), f"{base}_sim_recolor"),
            "crop": save(v_crop(mm.logo), f"{base}_sim_crop"),
            "jpeg": save(v_jpeg(mm.logo), f"{base}_sim_jpeg"),
        }
    sim_numbers = {nsv.profile.id: "0798 999 711", kg.profile.id: "0798 999 722", pt.profile.id: "0798 999 733"}
    for mm in MERCHANTS:
        m = mm.profile
        h = next(x.handle for x in m.official_handles if x.platform == "instagram")
        words = m.business_name.lower().split()
        styles = {
            "suffix": f"{h}_official_ke",
            "homoglyph": homoglyph(h),
            "underscore": "_".join(words),
        }
        for style, handle in styles.items():
            for logo, (avatar_url, feats) in variants[m.id].items():
                for pay in ("phone", "pochi", "none"):
                    for tokens in (True, False):
                        bio = f"{mm.category}, {mm.location}."
                        if pay == "phone":
                            bio += f" Order on WhatsApp {sim_numbers[m.id]}."
                        elif pay == "pochi":
                            bio += f" Tuma pesa kwa Pochi la Biashara {sim_numbers[m.id]}."
                        if tokens:
                            bio += " Lipa kwanza, pay before delivery. Offer ends today."
                        name = m.business_name + (" Official" if style == "suffix" else "")
                        created = TODAY - timedelta(days=2)
                        tp = target_profile(handle, name, bio, feats, 38, 4, created)
                        result, elapsed = score(tp)
                        key = f"{m.slug}|{style}|{logo}|{pay}|{int(tokens)}"
                        tid = uid("sim-threat", key) if result.verdict in ("impersonation", "suspicious") else None
                        tj = target_json(handle, name, avatar_url, 38, 4, created)
                        tj["fetched_via"] = "simulator"
                        sim[key] = check_result(uid("sim-scan", key), tj, tp, result, elapsed, tid)

    def dump(name: str, data, indent: int | None = 2) -> None:
        text = json.dumps(data, indent=indent, ensure_ascii=False)
        (OUT_JSON / name).write_text(text + "\n", encoding="utf-8")

    dump("checks.json", checks)
    dump("threats.json", threats)
    dump("alerts.json", alerts)
    dump("payments.json", payments)
    dump("merchants.json", [public_profile(m) for m in MERCHANTS])
    dump("stats.json", stats)
    dump("playbooks.json", books)
    dump("reports.json", [{"reported_phone": n, "status": s} for n, s in REPORTS])
    # every tweak combination is ~700 KB of repetitive JSON: store it gzipped (read server-side only)
    raw = json.dumps(sim, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (OUT_JSON / "simulator.json.gz").write_bytes(gzip.compress(raw, 9, mtime=0))
    sim_verdicts: dict[str, int] = {}
    for r in sim.values():
        sim_verdicts[r["verdict"]] = sim_verdicts.get(r["verdict"], 0) + 1
    print(f"simulator combos: {len(sim)} {sim_verdicts}")


SEED_DIR = OUT_JSON / "seed"
DERIVED_DIR = OUT_JSON / "derived"
OUT_PUBLIC = ROOT / "frontend" / "public" / "fixtures"
LOOKALIKE_HANDLE = "sneakervault_resale_ke"
LOOKALIKE_NAME = "Sneaker Vault Resale KE"
LOOKALIKE_BIO = "Pre-owned and new kicks. Viewing by appointment in Nairobi."


def derive_from_seed() -> None:
    """Extras the backend seed doesn't include, scored by the real engine against the SEED merchants:

    - simulator.json.gz: every POST /simulator/clone tweak combination (offline stage demo), built
      with the backend's own clone rules (app.services.simulator) and logo edits (fixtures.logos).
    - lookalike.json: a manual-input check (logo re-posted with a RESALE banner) that lands in
      `suspicious`, so the fourth verdict can be demonstrated from a chip. The chip uploads the same
      PNG bytes to the live API, which scores it identically.
    """
    from types import SimpleNamespace

    from app.ingestion.fixtures import logos as L
    from app.services.simulator import SIMULATOR_PHONE_LOCAL, clone_bio, clone_handle

    seed_merchants = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(SEED_DIR.glob("merchant-*.json"))]
    if not seed_merchants:
        print("no seed merchants: skipping derived fixtures")
        return
    payments = json.loads((SEED_DIR / "verify-payment.json").read_text(encoding="utf-8"))
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_PUBLIC / "sim").mkdir(parents=True, exist_ok=True)
    (OUT_PUBLIC / "lookalike").mkdir(parents=True, exist_ok=True)

    def logo_img(url: str) -> Image.Image:
        return Image.open(SEED_DIR / "assets" / url.rsplit("/", 1)[-1]).convert("RGB")

    def feats_of(img: Image.Image) -> ImageFeatures:
        h = hasher.compute_hashes(imaging.normalize_image(L.png_bytes(img)))
        return ImageFeatures(phash=h.phash, dhash=h.dhash)

    profiles, by_id, logos = [], {}, {}
    for m in seed_merchants:
        official_phones = [p["normalized"] for p in payments.values()
                           if p["status"] == "official" and p["kind"] == "phone" and (p.get("merchant") or {}).get("id") == m["id"]]
        logos[m["id"]] = logo_img(m["logo_url"])
        prof = MerchantProfile(
            id=m["id"], business_name=m["business_name"], slug=m["slug"],
            official_handles=tuple(OfficialHandle(h["platform"], h["handle"]) for h in m["official_handles"]),
            logo=feats_of(logos[m["id"]]), phone_numbers=tuple(official_phones),
            mpesa_type=m["payment"]["type"], mpesa_number=m["payment"]["number"],
            mpesa_account_name=m["payment"]["account_name"],
            established_on=date.fromisoformat(m["established_on"]) if m.get("established_on") else None,
        )
        profiles.append(prof)
        by_id[m["id"]] = m

    def matched_seed(p: MerchantProfile) -> dict:
        m = by_id[p.id]
        return {k: m[k] for k in ("id", "business_name", "slug", "logo_url", "official_handles", "payment")}

    def result_json(scan_id, tj, tp, result, elapsed, threat_id) -> dict:
        m = result.merchant
        hashes = None
        if result.visual is not None and tp.avatar is not None:
            ref = m.logo if m is not None else min((p.logo for p in profiles), key=lambda f: hasher.hamming(f.phash, tp.avatar.phash))
            hashes = {"target_phash": tp.avatar.phash, "reference_phash": ref.phash,
                      "hamming_distance": hasher.hamming(tp.avatar.phash, ref.phash)}
        safe = None
        if m is not None:
            en, sw = safe_action(m, tp.platform)
            safe = {"text": en, "text_sw": sw}
        return {
            "scan_id": scan_id, "verdict": result.verdict, "score": round(result.score, 2),
            "confidence": result.confidence, "target": tj,
            "matched_merchant": matched_seed(m) if m is not None else None,
            "dimensions": [] if result.verdict == "official" else result.dimensions_payload(),
            "reasons": result.reasons_payload(), "hashes": hashes, "safe_action": safe,
            "threat_id": threat_id, "elapsed_ms": elapsed,
        }

    def run(tp: TargetProfile):
        start = time.perf_counter()
        r = score_against_all(tp, profiles, ScoringContext(today=TODAY))
        return r, max(1, round((time.perf_counter() - start) * 1000))

    # simulator: keyed by merchant SLUG so it survives re-seeding with new ids
    sim = {}
    edits = {"exact": lambda i: i, "recolor": L.recolor, "crop": L.crop, "jpeg": L.jpeg}
    created = TODAY - timedelta(days=3)
    for prof in profiles:
        m = by_id[prof.id]
        rec = SimpleNamespace(business_name=m["business_name"], slug=m["slug"],
                              official_handles=[SimpleNamespace(**h) for h in m["official_handles"]])
        for logo_key, edit in edits.items():
            img = edit(logos[prof.id])
            thumb = img.resize((160, 160), Image.LANCZOS)
            thumb_path = OUT_PUBLIC / "sim" / f"{m['slug']}_{logo_key}.png"
            thumb.save(thumb_path, "PNG", optimize=True)
            feats = feats_of(img)
            for style in ("suffix", "homoglyph", "underscore"):
                handle = clone_handle(rec, style)
                name = f"{m['business_name']} Official" if style == "suffix" else m["business_name"]
                for pay in ("phone", "pochi", "none"):
                    for tokens in (True, False):
                        bio = clone_bio(rec, SimpleNamespace(payment=pay, bio_tokens=tokens))
                        tp = TargetProfile(platform="instagram", handle=handle, display_name=name, bio=bio,
                                           avatar=feats, payment=extract_payment_evidence(bio),
                                           follower_count=60, post_count=4, account_created_on=created)
                        r, ms = run(tp)
                        key = f"{m['slug']}|{style}|{logo_key}|{pay}|{int(tokens)}"
                        tid = uid("sim-threat", m["slug"], style) if r.merchant is not None and r.score >= 70 else None
                        tj = target_json(handle, name, f"/fixtures/sim/{thumb_path.name}", 60, 4, created)
                        tj["fetched_via"] = "simulator"
                        sim[key] = result_json(uid("sim-scan", key), tj, tp, r, ms, tid)
    raw = json.dumps(sim, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (DERIVED_DIR / "simulator.json.gz").write_bytes(gzip.compress(raw, 9, mtime=0))
    counts: dict[str, int] = {}
    for r in sim.values():
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"derived simulator combos: {len(sim)} {counts} (phone {SIMULATOR_PHONE_LOCAL})")

    # look-alike (manual input): the registered NSV logo re-posted with a RESALE banner
    nsv = next(p for p in profiles if p.slug == "nairobi-sneaker-vault")
    img = logos[nsv.id].resize((96, 96), Image.LANCZOS).resize((400, 400), Image.BICUBIC)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 318, 400, 370), fill="#C8102E")
    fnt = ImageFont.truetype(str(FONTS / "arialbd.ttf"), 30) if (FONTS / "arialbd.ttf").exists() else None
    d.text(((400 - d.textlength("RESALE", font=fnt)) / 2, 326), "RESALE", font=fnt, fill="#FFFFFF")
    path = OUT_PUBLIC / "lookalike" / f"{LOOKALIKE_HANDLE}.png"
    img.save(path, "PNG", optimize=True)
    data = path.read_bytes()
    h = hasher.compute_hashes(imaging.normalize_image(data))  # exactly what the API computes from the upload
    tp = TargetProfile(platform="instagram", handle=LOOKALIKE_HANDLE, display_name=LOOKALIKE_NAME,
                       bio=LOOKALIKE_BIO, avatar=ImageFeatures(phash=h.phash, dhash=h.dhash),
                       payment=extract_payment_evidence(LOOKALIKE_BIO))
    r, ms = run(tp)
    tid = uid("lookalike-threat") if r.merchant is not None and r.score >= 70 else None
    tj = target_json(LOOKALIKE_HANDLE, LOOKALIKE_NAME, None, None, None, None)
    tj["fetched_via"] = "manual"
    look = result_json(uid("lookalike-scan"), tj, tp, r, ms, tid)
    (DERIVED_DIR / "lookalike.json").write_text(json.dumps([look], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"derived look-alike: {r.verdict} {r.score} conf {r.confidence} rules {r.rules}")


def homoglyph(h: str) -> str:
    for a, b in (("l", "1"), ("o", "0"), ("i", "1"), ("e", "3")):
        idx = h.rfind(a)
        if idx >= 0:
            return h[:idx] + b + h[idx + 1:]
    return h + "_"


if __name__ == "__main__":
    main()
    derive_from_seed()
