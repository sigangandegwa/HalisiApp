import pytest
from typing import Optional
from app.engine.matcher import identity_score, language_score

class DummyHandle:
    def __init__(self, handle: str):
        self.handle = handle

class DummyMerchant:
    def __init__(self, handles: list[str], name: str = "", aliases: Optional[list[str]] = None):
        self.official_handles = [DummyHandle(h) for h in handles]
        self.business_name = name
        self.aliases = aliases or []

@pytest.mark.parametrize("official, target, min_score, max_score", [
    ("nairobisneakervault", "nairobi_sneakervault_official_ke", 90, 100),
    ("nairobisneakervault", "nairobisneakervau1t", 90, 100),
    ("nairobisneakervault", "nairobi.sneaker.vault", 95, 100),
    ("kilimaniglow", "kiIimaniglow_ke", 90, 100), # capital i
    ("nairobisneakervault", "nairobi_bakery", 0, 80),
    ("nairobisneakervault", "nairobisneakerhub", 0, 90),
    ("pwanithreads", "mombasa_fashion_house", 0, 40),
])
def test_identity_score_golden(official, target, min_score, max_score):
    merchant = DummyMerchant([official])
    result = identity_score(target, None, merchant)
    assert min_score <= result.score <= max_score, f"Expected {min_score}-{max_score} for '{target}' against '{official}', got {result.score}. Evidence: {result.evidence}"

def test_language_score():
    bio = "Welcome to our shop. Pay before delivery and get 10% off. Offer ends today!"
    res = language_score(bio)
    assert res.score == 65.0
    assert "pay before delivery" in res.evidence
    assert "offer ends today" in res.evidence

def test_language_score_capped():
    bio = "Pay before delivery. Lipa kwanza. No refunds. Strictly delivery. Order now."
    res = language_score(bio)
    assert res.score == 100.0

def test_language_score_none():
    res = language_score("Just a normal bio")
    assert res.score is None
    assert res.evidence is None
