import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
import logging

logger = logging.getLogger(__name__)

async def upload_progress(current, total, event, start_time, msg_text="Uploading..."):
    """Callback function for upload progress with bar and ETA."""
    import time
    percentage = (current / total) * 100
    
    # Avoid flood: update every 5% or so
    if not hasattr(upload_progress, "last_percent"):
        upload_progress.last_percent = 0
    
    if abs(percentage - upload_progress.last_percent) < 5 and percentage < 100:
        return

    upload_progress.last_percent = percentage
    
    elapsed_time = time.time() - start_time
    if current > 0:
        speed = current / elapsed_time # bytes per second
        remaining_bytes = total - current
        eta_seconds = remaining_bytes / speed
        eta_str = time.strftime("%M:%S", time.gmtime(eta_seconds))
    else:
        eta_str = "--:--"

    # Simple bar
    length = 15
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    
    progress_text = (
        f"{msg_text}\n"
        f"|{bar}| {percentage:.1f}%\n"
        f"⏳ ETA: {eta_str} | 🚀 {current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB"
    )
    
    try:
        await event.edit(progress_text)
    except:
        pass

async def upload_drama(client: TelegramClient, chat_id: int, 
                       title: str, description: str, 
                       poster_url: str, video_path: str,
                       reply_to=None):
    """
    Uploads the drama information and merged video to Telegram.
    """
    import subprocess
    import tempfile
    import time
    try:
        # 1. Send Poster + Description as PHOTO
        caption = f"🎬 **{title}**\n\n📝 **Sinopsis:**\n{description[:500]}..."
        
        import httpx
        poster_path = None
        try:
            async with httpx.AsyncClient(timeout=30) as http_client:
                resp = await http_client.get(poster_url)
                if resp.status_code == 200:
                    poster_path = os.path.join(tempfile.gettempdir(), f"poster_{int(time.time())}.jpg")
                    with open(poster_path, "wb") as pf:
                        pf.write(resp.content)
        except Exception as e:
            logger.warning(f"Failed to download poster: {e}")
        
        await client.send_file(
            chat_id,
            poster_path or poster_url,
            caption=caption,
            parse_mode='md',
            force_document=False,
            reply_to=reply_to
        )
        
        if poster_path and os.path.exists(poster_path):
            os.remove(poster_path)
        
        status_msg = await client.send_message(chat_id, "📤 Ekstraksi Thumbnail & Durasi...", reply_to=reply_to)
        
        # 2. Extract Duration & Dimensions
        duration = 0
        width = 0
        height = 0
        try:
            ffprobe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            output = subprocess.check_output(ffprobe_cmd, text=True).strip().split('\n')
            if len(output) >= 3:
                width = int(output[0])
                height = int(output[1])
                duration = int(float(output[2]))
        except Exception as e:
            logger.warning(f"Failed to extract video info: {e}")

        # 3. Extract Thumbnail
        thumb_path = os.path.join(tempfile.gettempdir(), f"thumb_{int(time.time())}.jpg")
        try:
            subprocess.run(["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:01.000", "-vframes", "1", thumb_path], capture_output=True)
            if not os.path.exists(thumb_path):
                thumb_path = None
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            thumb_path = None

        await status_msg.edit("📤 Sedang mengupload video ke Telegram...")
        
        from telethon.tl.types import DocumentAttributeVideo
        video_attributes = [
            DocumentAttributeVideo(
                duration=duration,
                w=width,
                h=height,
                supports_streaming=True
            )
        ]
        
        start_time = time.time()
        await client.send_file(
            chat_id,
            video_path,
            caption=f"🎥 Full Episode: {title}",
            force_document=False,
            thumb=thumb_path,
            attributes=video_attributes,
            progress_callback=lambda c, t: upload_progress(c, t, status_msg, start_time, "Upload Video:"),
            supports_streaming=True,
            reply_to=reply_to
        )
        
        await status_msg.delete()
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        logger.info(f"Successfully uploaded {title} to Telegram")
        return True
    except Exception as e:
        logger.error(f"Failed to upload to Telegram: {e}")
        return False
        
        await status_msg.delete()
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        logger.info(f"Successfully uploaded {title} to Telegram")
        return True
    except Exception as e:
        logger.error(f"Failed to upload to Telegram: {e}")
        return False
