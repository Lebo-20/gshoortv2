import os
import asyncio
import httpx
import logging
import subprocess

logger = logging.getLogger(__name__)

async def download_file_ffmpeg(url: str, path: str):
    """Downloads an m3u8 (or any stream) using ffmpeg and converts it to mp4."""
    try:
        # ffmpeg -i url -c copy -bsf:a aac_adtstoasc output.mp4
        # We use await asyncio.create_subprocess_exec for non-blocking execution
        command = [
            "ffmpeg", "-y", 
            "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
            "-i", url,
            "-c", "copy", "-bsf:a", "aac_adtstoasc",
            path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True
        else:
            error_msg = stderr.decode().strip()
            logger.error(f"FFmpeg failed for {url}: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Exception during ffmpeg download of {url}: {e}")
        return False

async def download_file_http(client: httpx.AsyncClient, url: str, path: str, progress_callback=None):
    """Downloads a single file via HTTP (original method)."""
    try:
        async with client.stream("GET", url) as response:
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} for {url}")
                return False
                
            total_size = int(response.headers.get("Content-Length", 0))
            download_size = 0
            
            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    download_size += len(chunk)
                    if progress_callback:
                        await progress_callback(download_size, total_size)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

async def download_all_episodes(episodes, download_dir: str, semaphore_count: int = 5):
    """
    Downloads all episodes concurrently.
    Correctly handles both direct MP4 links and m3u8 playlists via proxy.
    """
    os.makedirs(download_dir, exist_ok=True)
    semaphore = asyncio.Semaphore(semaphore_count)

    tasks = []
    
    async def limited_download(ep):
        async with semaphore:
            # Normalize episode number for ranking
            ep_num = str(ep.get('episode', 'unk')).zfill(3)
            filename = f"episode_{ep_num}.mp4"
            filepath = os.path.join(download_dir, filename)
            
            url = None
            videos = ep.get('videos', [])
            if isinstance(videos, list) and videos:
                # Prefer highest quality
                url = videos[0].get('url')
                for video in videos:
                    if video.get('quality') in ['1080P', '720P']:
                        url = video.get('url')
                        break

            if not url:
                logger.error(f"No URL found for episode {ep_num}")
                return False
            
            # Use ffmpeg for m3u8 (proxy URLs), otherwise use HTTP
            if "m3u8" in url or ".m3u8" in url:
                success = await download_file_ffmpeg(url, filepath)
            else:
                async with httpx.AsyncClient(timeout=60) as client:
                    success = await download_file_http(client, url, filepath)
            
            if success:
                logger.info(f"Downloaded {filename}")
            else:
                logger.error(f"Failed to download episode {ep_num}")
                
            return success

    results = await asyncio.gather(*(limited_download(ep) for ep in episodes))
    return all(results)
