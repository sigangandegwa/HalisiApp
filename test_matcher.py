from backend.app.engine.matcher import calculate_typosquatting_score, analyze_bio_scam_tokens, analyze_text_match

def run_tests():
    print("Running matcher tests...")
    
    auth_handle = "@nairobi_shoes_official"
    scam_handle = "@nairobl_shoes_oficial" # Subtle character changes (i to l, missing f)
    
    typo_score = calculate_typosquatting_score(auth_handle, scam_handle)
    print(f"Jaro-Winkler Typosquatting Score: {typo_score}%")
    
    bio = "Welcome to the best shoe store in Kenya. Strictly delivery! Pay before delivery via Till 123456."
    bio_risk = analyze_bio_scam_tokens(bio)
    print(f"Bio Token Risk Score: {bio_risk}%")
    
    if typo_score > 85 and bio_risk > 50:
        print("✅ TEST PASSED: Matcher correctly flagged typosquatting and scam tokens.")
    else:
        print("❌ TEST FAILED: Scores did not meet the expected thresholds.")

if __name__ == "__main__":
    run_tests()
