import asyncio
import httpx
import os

PROXY_URL = "http://localhost:3100"

async def test_download(book_id, chapter_id):
    async with httpx.AsyncClient(timeout=30) as client:
        print(f"Fetching m3u8 for chapter {chapter_id}...")
        resp = await client.get(f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}")
        if resp.status_code != 200:
            print(f"Failed to fetch m3u8: {resp.status_code}")
            return
        
        m3u8_content = resp.text
        lines = m3u8_content.split('\n')
        segments = [l for l in lines if l.strip() and not l.startswith('#')]
        print(f"Found {len(segments)} segments in m3u8.")
        
        if segments:
            first_segment_url = segments[0]
            print(f"Testing first segment: {first_segment_url}")
            seg_resp = await client.get(first_segment_url)
            print(f"Segment response status: {seg_resp.status_code}")
            print(f"Segment size: {len(seg_resp.content)} bytes")
            if len(seg_resp.content) < 1000:
                print("WARNING: Segment is very small!")
                print(f"Segment content start: {seg_resp.content[:100]}")

if __name__ == "__main__":
    book_id = "31001370470"
    chapter_id = "18094613"
    asyncio.run(test_download(book_id, chapter_id))
