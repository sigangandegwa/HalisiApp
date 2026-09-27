import argparse
import json
import os
import shutil
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imagehash

from typing import Dict, List, Any
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imagehash

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_FIXTURES_DIR = BASE_DIR / "backend" / "app" / "ingestion" / "fixtures"
FRONTEND_FIXTURES_DIR = BASE_DIR / "frontend" / "src" / "lib" / "fixtures"

def generate_logo(name: str, color: str, filepath: Path) -> Image.Image:
    # 256x256 image
    img = Image.new("RGB", (256, 256), color=color)
    d = ImageDraw.Draw(img)
    # Just draw text in the middle
    d.text((50, 120), name, fill="white")
    img.save(filepath)
    return img

def create_variants(base_img: Image.Image, name: str, filepath_base: str):
    # variant 1: recolor (blatant clone uses exact logo, subtle uses recolored)
    # variant 2: crop 85%
    # variant 3: downscale 64px
    
    # We will just generate and save them
    subtle_img = Image.new("RGB", (256, 256), color="darkred")
    d = ImageDraw.Draw(subtle_img)
    d.text((50, 120), name + " (Clone)", fill="white")
    subtle_img.save(f"{filepath_base}_subtle.png")
    
    competitor_img = Image.new("RGB", (256, 256), color="green")
    d = ImageDraw.Draw(competitor_img)
    d.text((50, 120), name + " Hub", fill="white")
    competitor_img.save(f"{filepath_base}_competitor.png")
    
    return subtle_img, competitor_img

def compute_phash(img: Image.Image) -> str:
    return str(imagehash.phash(img))

def compute_dhash(img: Image.Image) -> str:
    return str(imagehash.dhash(img))

def run_seeder(target: str, reset: bool):
    os.makedirs(BACKEND_FIXTURES_DIR / "assets", exist_ok=True)
    os.makedirs(FRONTEND_FIXTURES_DIR / "assets", exist_ok=True)

    # 1. Nairobi Sneaker Vault
    nsv_logo = generate_logo("NSV", "blue", BACKEND_FIXTURES_DIR / "assets" / "nsv.png")
    nsv_subtle, nsv_comp = create_variants(nsv_logo, "NSV", str(BACKEND_FIXTURES_DIR / "assets" / "nsv"))
    
    # 2. Kilimani Glow
    kg_logo = generate_logo("KG", "purple", BACKEND_FIXTURES_DIR / "assets" / "kg.png")
    kg_subtle, kg_comp = create_variants(kg_logo, "KG", str(BACKEND_FIXTURES_DIR / "assets" / "kg"))

    # 3. Pwani Threads
    pt_logo = generate_logo("PT", "orange", BACKEND_FIXTURES_DIR / "assets" / "pt.png")
    pt_subtle, pt_comp = create_variants(pt_logo, "PT", str(BACKEND_FIXTURES_DIR / "assets" / "pt"))
    
    merchants = []
    threats = []
    reports = []
    
    def make_merchant(id_str, name, slug, logo_name, img, till, handle):
        return {
            "id": id_str,
            "business_name": name,
            "slug": slug,
            "aliases": [],
            "category": "Retail",
            "location": "Nairobi",
            "established_on": "2020-01-01",
            "logo_url": f"/fixtures/assets/{logo_name}.png",
            "logo_phash": compute_phash(img),
            "logo_dhash": compute_dhash(img),
            "mpesa_type": "till",
            "mpesa_number": till,
            "phone_numbers": [],
            "is_verified": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "official_handles": [{"platform": "instagram", "handle": handle, "url": f"https://instagram.com/{handle}"}]
        }
        
    m1 = make_merchant(str(uuid.uuid4()), "Nairobi Sneaker Vault", "nairobi-sneaker-vault", "nsv", nsv_logo, "111111", "nairobisneakervault")
    m2 = make_merchant(str(uuid.uuid4()), "Kilimani Glow", "kilimani-glow", "kg", kg_logo, "222222", "kilimaniglow")
    m3 = make_merchant(str(uuid.uuid4()), "Pwani Threads", "pwani-threads", "pt", pt_logo, "333333", "pwanithreads")
    merchants.extend([m1, m2, m3])

    def make_threat(m_id, suffix, handle, img, phone, tokens, age, comp_score, logo_name):
        return {
            "id": str(uuid.uuid4()),
            "merchant_id": m_id,
            "platform": "instagram",
            "target_handle": handle,
            "status": "detected" if comp_score >= 70 else "dismissed",
            "confidence": 0.9,
            "composite_score": comp_score,
            "evidence": {
                "visual": {"score": 100 if "official" in suffix else 40, "phash": compute_phash(img)},
                "identity": {"score": 90, "matched_handle": handle},
                "payment": {"score": 100 if phone else 0, "extracted_phones": [phone] if phone else []},
                "language": {"score": len(tokens)*10, "scam_tokens": tokens},
                "account": {"score": 60, "age_days": age}
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "avatar_url": f"/fixtures/assets/{logo_name}.png"
        }

    # Generate 3 threats for NSV
    threats.append(make_threat(m1["id"], "blatant", "nairobi_sneakervault_official_ke", nsv_logo, "+254711111111", ["pay before delivery"], 8, 95, "nsv"))
    threats.append(make_threat(m1["id"], "subtle", "nairobisneakervau1t", nsv_subtle, None, ["pochi la biashara"], None, 75, "nsv_subtle"))
    threats.append(make_threat(m1["id"], "legit", "nairobisneakerhub", nsv_comp, "+254722222222", [], 1000, 30, "nsv_competitor"))

    # Generate 3 threats for KG
    threats.append(make_threat(m2["id"], "blatant", "kilimaniglow_official_ke", kg_logo, "+254733333333", ["no refunds"], 5, 95, "kg"))
    threats.append(make_threat(m2["id"], "subtle", "kiIimaniglow_ke", kg_subtle, None, ["send money to"], None, 75, "kg_subtle"))
    threats.append(make_threat(m2["id"], "legit", "kilimanibeauty", kg_comp, "+254744444444", [], 1000, 30, "kg_competitor"))

    # Generate 3 threats for PT
    threats.append(make_threat(m3["id"], "blatant", "pwanithreads_official_ke", pt_logo, "+254755555555", ["deposit required"], 8, 95, "pt"))
    threats.append(make_threat(m3["id"], "subtle", "pwanlthreads", pt_subtle, None, ["tuma pesa"], None, 75, "pt_subtle"))
    threats.append(make_threat(m3["id"], "legit", "mombasa_fashion_house", pt_comp, "+254766666666", [], 1000, 20, "pt_competitor"))

    # 5 community reports (2 confirmed) pointing at blatant clones
    reports = [
        {"id": str(uuid.uuid4()), "threat_id": threats[0]["id"], "reported_phone": "+254711111111", "status": "confirmed", "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "threat_id": threats[3]["id"], "reported_phone": "+254733333333", "status": "confirmed", "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "threat_id": threats[6]["id"], "reported_phone": "+254755555555", "status": "pending", "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "threat_id": threats[0]["id"], "reported_phone": "+254711111111", "status": "pending", "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "threat_id": threats[3]["id"], "reported_phone": "+254733333333", "status": "pending", "created_at": datetime.now().isoformat()}
    ]

    # Save to JSON
    with open(BACKEND_FIXTURES_DIR / "merchants.json", "w") as f:
        json.dump(merchants, f, indent=2)
    with open(BACKEND_FIXTURES_DIR / "threats.json", "w") as f:
        json.dump(threats, f, indent=2)
    with open(BACKEND_FIXTURES_DIR / "reports.json", "w") as f:
        json.dump(reports, f, indent=2)

    # Copy to frontend
    shutil.copytree(BACKEND_FIXTURES_DIR, FRONTEND_FIXTURES_DIR, dirs_exist_ok=True)
    
    print(f"Mock seeder finished. Target: {target}, Reset: {reset}")
    print(f"Generated {len(merchants)} merchants, {len(threats)} threats, {len(reports)} reports.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["supabase", "memory"], default="memory")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    
    run_seeder(args.target, args.reset)
