import asyncio
import os
import httpx
import subprocess
from downloader import download_m3u8

PROXY_URL = "http://localhost:3100"

async def test_video_duration(chapter_id, book_id):
    print(f"Testing Chapter: {chapter_id} Book: {book_id}")
    
    # 1. Load book into proxy
    async with httpx.AsyncClient(timeout=30) as client:
        print("Loading book into proxy...")
        resp = await client.get(f"{PROXY_URL}/load/{book_id}")
        print(f"Proxy Load: {resp.status_code} {resp.text}")

    # 2. Download 1 episode
    filename = "test_episode.mp4"
    if os.path.exists(filename): os.remove(filename)
    
    proxy_url = f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}"
    print(f"Downloading via proxy: {proxy_url}")
    
    # Debug: Lihat isi m3u8
    async with httpx.AsyncClient(timeout=60) as client:
        r_m3u8 = await client.get(proxy_url)
        print("--- M3U8 CONTENT START ---")
        print(r_m3u8.text)
        print("--- M3U8 CONTENT END ---")

    success = await download_m3u8(proxy_url, filename)
    if not success:
        print("Download failed.")
        return

    # 3. Check duration with ffprobe
    print("Checking duration with ffprobe...")
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        print(f"DURATION: {output} seconds")
        if float(output) < 20:
            print("WARNING: Duration is very short (likely a preview).")
    except Exception as e:
        print(f"Failed to get duration: {e}")

if __name__ == "__main__":
    # Use a known book and chapter ID from previous logs
    # Book: 31001345253, Chapter: 17726025
    asyncio.run(test_video_duration("18344332", "31001380505"))
