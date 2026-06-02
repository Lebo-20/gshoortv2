import asyncio
import httpx
from api import get_all_episodes

async def test_ep(book_id, ep_index=10):
    episodes = await get_all_episodes(book_id)
    if len(episodes) <= ep_index:
        print(f"Not enough episodes. Found {len(episodes)}")
        return
    
    ep = episodes[ep_index]
    chapter_id = ep.get('id')
    print(f"Testing Episode {ep_index+1} (ID: {chapter_id})")
    
    PROXY_URL = "http://localhost:3100"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}")
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code}")
            return
        
        m3u8_content = resp.text
        lines = m3u8_content.split('\n')
        segments = [l for l in lines if l.strip() and not l.startswith('#')]
        print(f"Found {len(segments)} segments.")
        
        # Calculate total duration if possible
        duration = 0
        for line in lines:
            if line.startswith('#EXTINF:'):
                try:
                    duration += float(line.split(':')[1].split(',')[0])
                except:
                    pass
        print(f"Total duration in m3u8: {duration} seconds")

if __name__ == "__main__":
    book_id = "31001370470"
    asyncio.run(test_ep(book_id, 10)) # Test episode 11
