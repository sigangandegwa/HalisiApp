import pytest
from app.ingestion.extractors import extract_payment_signals

@pytest.mark.parametrize("text, expected", [
    ("Call us on 0712345678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": False}),
    ("WhatsApp +254 712 345 678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": False}),
    ("wa.me/254712345678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": False}),
    ("Till no 123456", {"phones": [], "tills": ["123456"], "paybills": [], "has_pochi": False}),
    ("Buy goods 123456", {"phones": [], "tills": ["123456"], "paybills": [], "has_pochi": False}),
    ("B.G. 123456", {"phones": [], "tills": ["123456"], "paybills": [], "has_pochi": False}),
    ("Paybill 987654", {"phones": [], "tills": [], "paybills": ["987654"], "has_pochi": False}),
    ("Send money to 0712 345 678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": True}),
    ("Pochi la biashara", {"phones": [], "tills": [], "paybills": [], "has_pochi": True}),
    ("Tuma pesa kwa 0112345678", {"phones": ["+254112345678"], "tills": [], "paybills": [], "has_pochi": True}),
    ("Till: 12345, Call +254711222333", {"phones": ["+254711222333"], "tills": ["12345"], "paybills": [], "has_pochi": False}),
    ("No phone, no till", {"phones": [], "tills": [], "paybills": [], "has_pochi": False})
])
def test_payment_extractors(text, expected):
    res = extract_payment_signals(text)
    assert sorted(res["phones"]) == sorted(expected["phones"])
    assert sorted(res["tills"]) == sorted(expected["tills"])
    assert sorted(res["paybills"]) == sorted(expected["paybills"])
    assert res["has_pochi"] == expected["has_pochi"]
