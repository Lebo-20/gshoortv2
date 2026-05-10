import os
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

PROXY_URL = "http://localhost:3100"

async def download_m3u8(url: str, path: str):
    """Downloads an m3u8 playlist using ffmpeg."""
    try:
        # Use simple ffmpeg command as proxy handles the key and segments
        cmd = [
            "ffmpeg", "-y", 
            "-user_agent", "okhttp/3.12.13",
            "-allowed_extensions", "ALL",
            "-i", url,
            "-c", "copy", "-bsf:a", "aac_adtstoasc",
            "-loglevel", "error",
            path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        if stderr:
            print(f"--- FFmpeg Log ---\n{stderr.decode()}\n------------------")
            
        if process.returncode == 0:
            return True
        else:
            logger.error(f"FFmpeg failed: {stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"FFmpeg exception: {e}")
        return False

async def download_all_episodes(episodes, download_dir: str, book_id: str = None, semaphore_count: int = 5, progress_callback=None):
    """
    Downloads all episodes via GoodShort Proxy.
    """
    os.makedirs(download_dir, exist_ok=True)
    
    # 1. Load book into proxy cache
    if book_id:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                logger.info(f"📡 Loading book {book_id} into proxy...")
                resp = await client.get(f"{PROXY_URL}/load/{book_id}")
                if resp.status_code != 200:
                    logger.error(f"Failed to load book into proxy: {resp.text}")
                    # Continue anyway, proxy might try to auto-fetch
        except Exception as e:
            logger.error(f"Proxy connection error: {e}")

    semaphore = asyncio.Semaphore(semaphore_count)
    total = len(episodes)
    completed = 0

    async def limited_download(ep):
        nonlocal completed
        async with semaphore:
            # GoodShort uses 'id' for chapters
            chapter_id = ep.get('id') or ep.get('vid')
            vid = ep.get('vid') or ep.get('episode') or chapter_id or 'unk'
            ep_num = str(vid).zfill(3)
            filename = f"episode_{ep_num}.mp4"
            filepath = os.path.join(download_dir, filename)
            
            # Point to proxy m3u8 endpoint
            proxy_m3u8_url = f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}"
            
            logger.info(f"📥 Downloading episode {ep_num} via Proxy...")
            success = await download_m3u8(proxy_m3u8_url, filepath)
            
            if success:
                completed += 1
                file_size = os.path.getsize(filepath) / (1024 * 1024) # Convert to MB
                if progress_callback:
                    await progress_callback(completed, total)
                logger.info(f"✅ Downloaded {filename} ({file_size:.2f} MB) ({completed}/{total})")
            return success

    results = await asyncio.gather(*(limited_download(ep) for ep in episodes))
    return all(results)
