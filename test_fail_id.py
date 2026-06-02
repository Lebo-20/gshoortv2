import asyncio
import httpx
from api import get_drama_detail, get_all_episodes

async def test_drama(book_id):
    detail = await get_drama_detail(book_id)
    title = detail.get('title') if detail else "Unknown"
    print(f"Drama: {title} (ID: {book_id})")
    
    episodes = await get_all_episodes(book_id)
    if not episodes:
        print("No episodes found.")
        return
    
    ep = episodes[0]
    chapter_id = ep.get('id')
    print(f"Episode 1 ID: {chapter_id}")
    
    PROXY_URL = "http://localhost:3100"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}")
        if resp.status_code != 200:
            print(f"Proxy Error: {resp.status_code}")
            return
        
        m3u8 = resp.text
        duration = 0
        for line in m3u8.split('\n'):
            if line.startswith('#EXTINF:'):
                duration += float(line.split(':')[1].split(',')[0])
        print(f"Duration: {duration} seconds")

if __name__ == "__main__":
    import sys
    # Test one of the IDs from failures.json
    asyncio.run(test_drama("31001049662"))
