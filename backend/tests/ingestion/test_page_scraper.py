import pytest
import httpx
import respx
from app.ingestion.page_scraper import scrape_profile, TargetUnreachable
from app.engine.scorer import TargetProfile
from app.schemas.check import ManualTarget
from app.schemas.threat import ThreatRecord
import uuid
from datetime import datetime
from unittest.mock import patch

class DummyRepo:
    def __init__(self, threat=None):
        self.threat = threat
    
    async def find_threat_by_target(self, platform: str, handle: str):
        if self.threat and self.threat.platform == platform and self.threat.target_handle == handle:
            return self.threat
        return None

@pytest.mark.asyncio
async def test_scrape_profile_tier1_seed():
    threat = ThreatRecord(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        platform="instagram",
        target_handle="scammer",
        target_url="https://instagram.com/scammer",
        display_name="Scam Store",
        composite_score=80.0,
        first_seen_at=datetime.now(),
        last_checked_at=datetime.now()
    )
    repo = DummyRepo(threat=threat)
    async with httpx.AsyncClient() as client:
        profile = await scrape_profile("instagram", "scammer", repo, client)
        
    assert profile.fetched_via == "seed"
    assert profile.display_name == "Scam Store"
    assert profile.platform == "instagram"
    assert profile.handle == "scammer"

@pytest.mark.asyncio
async def test_scrape_profile_tier2_manual():
    repo = DummyRepo()
    manual = ManualTarget(display_name="Manual Store", bio="Buy shoes here", avatar_base64="data:image/png;base64,iVBORw0KGgo=")
    async with httpx.AsyncClient() as client:
        profile = await scrape_profile("instagram", "unknown", repo, client, manual=manual)
        
    assert profile.fetched_via == "manual"
    assert profile.display_name == "Manual Store"
    assert profile.bio == "Buy shoes here"
    assert profile.avatar_bytes is not None and profile.avatar_bytes[:4] == b"\x89PNG"

@respx.mock
@patch('app.ingestion.page_scraper.is_public_url', return_value=True)
@pytest.mark.asyncio
async def test_scrape_profile_tier2_live(mock_is_public):
    repo = DummyRepo()
    html = """
    <html>
      <head>
        <meta property="og:title" content="Test Store (@teststore) • Instagram photos and videos" />
        <meta property="og:description" content="1,234 Followers, 56 Following, 78 Posts - See Instagram photos and videos from Test Store (@teststore)" />
        <meta property="og:image" content="https://example.com/image.jpg" />
      </head>
    </html>
    """
    respx.get("https://instagram.com/teststore").mock(return_value=httpx.Response(200, text=html))
    
    async with httpx.AsyncClient() as client:
        profile = await scrape_profile("instagram", "teststore", repo, client)
        
    assert profile.fetched_via == "live"
    assert profile.display_name == "Test Store"
    assert profile.follower_count == 1234
    assert profile.post_count == 78
    assert profile.avatar_url == "https://example.com/image.jpg"

@respx.mock
@patch('app.ingestion.page_scraper.is_public_url', return_value=True)
@pytest.mark.asyncio
async def test_scrape_profile_login_wall(mock_is_public):
    repo = DummyRepo()
    html = "<html><body>Login to continue</body></html>"
    respx.get("https://instagram.com/wall").mock(return_value=httpx.Response(200, text=html))
    
    async with httpx.AsyncClient() as client:
        with pytest.raises(TargetUnreachable) as exc:
            await scrape_profile("instagram", "wall", repo, client)
        assert "Login wall" in exc.value.message
