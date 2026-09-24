import asyncio
from backend.app.engine.hasher import compute_phash, compare_hashes

async def run_tests():
    print("Running hash tests...")
    
    # We will use two identical/similar images from public URLs
    # Example: Google logo
    img1_url = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
    img2_url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
    
    try:
        hash1 = await compute_phash(img1_url)
        print(f"Hash 1: {hash1}")
        
        hash2 = await compute_phash(img2_url)
        print(f"Hash 2: {hash2}")
        
        similarity = compare_hashes(hash1, hash2)
        print(f"Similarity Score: {similarity}%")
        
        if similarity > 90:
            print("✅ TEST PASSED: High similarity detected for identical logos.")
        else:
            print("❌ TEST FAILED: Low similarity score.")
            
    except Exception as e:
        print(f"❌ TEST ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_tests())
