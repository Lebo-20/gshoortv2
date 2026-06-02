import asyncio
import httpx
import os

PROXY_URL = "http://localhost:3100"

async def test_download(book_id, chapter_id):
    # 1. Load book into proxy
    async with httpx.AsyncClient(timeout=30) as client:
        print(f"Loading book {book_id} into proxy...")
        resp = await client.get(f"{PROXY_URL}/load/{book_id}")
        print(f"Load response: {resp.text}")
        
        # 2. Get m3u8 from proxy
        print(f"Fetching m3u8 for chapter {chapter_id}...")
        resp = await client.get(f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}")
        if resp.status_code != 200:
            print(f"Failed to fetch m3u8: {resp.status_code}")
            return
        
        m3u8_content = resp.text
        lines = m3u8_content.split('\n')
        segments = [l for l in lines if l.strip() and not l.startswith('#')]
        print(f"Found {len(segments)} segments in m3u8.")
        
        if len(segments) < 5:
            print("WARNING: Very few segments found. This is likely a preview.")
        
        # 3. Try to download using ffmpeg
        output_file = f"test_ep_{chapter_id}.mp4"
        cmd = [
            "ffmpeg", "-y", 
            "-i", f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}",
            "-t", "15", # limit to 15s to check if it even has that much
            "-c", "copy",
            output_file
        ]
        
        print(f"Running ffmpeg to download...")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            size = os.path.getsize(output_file)
            print(f"Download successful. File size: {size} bytes")
        else:
            print(f"Download failed: {stderr.decode()}")

if __name__ == "__main__":
    import sys
    book_id = "31001370470"
    chapter_id = "18094613"
    asyncio.run(test_download(book_id, chapter_id))
