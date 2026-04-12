import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
import logging

logger = logging.getLogger(__name__)

# Global variable to track last update time and percentage to avoid flood
last_update_data = {"time": 0, "percentage": -1}

async def upload_progress(current, total, event, msg_text="Uploading..."):
    """Callback function for upload progress with throttling to avoid flood wait."""
    import time
    global last_update_data
    
    percentage = int((current / total) * 100)
    now = time.time()
    
    # Only update if percentage has changed, is a multiple of 10, 
    # and at least 5 seconds have passed since last update
    if (percentage % 10 == 0) and (percentage != last_update_data["percentage"]) and (now - last_update_data["time"] > 5):
        try:
            last_update_data["percentage"] = percentage
            last_update_data["time"] = now
            await event.edit(f"{msg_text} {percentage}%")
        except Exception:
            pass

async def upload_drama(client: TelegramClient, chat_id: int, 
                       title: str, description: str, 
                       poster_url: str, video_path: str,
                       total_episodes: int = 0,
                       message_thread_id: int = None):
    """
    Uploads the final merged video to Telegram with a clean caption and thumbnail.
    """
    import subprocess
    import tempfile
    import httpx
    
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        logger.error(f"Cannot upload: Video file {video_path} does not exist or is empty.")
        return False
        
    try:
        # Prepare the poster URL
        if poster_url and poster_url.startswith("//"):
            poster_url = "https:" + poster_url
            
        # 1. Prepare Caption exactly like screenshot
        caption = (
            f"🎬 **{title}**\n\n"
            f"📝 **Sinopsis:**\n{description}"
        )
        
        # 2. Extract Duration & Dimensions (For video attributes)
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
 
        # 3. Download Thumbnail (poster)
        thumb_path = None
        if poster_url:
            try:
                # Telethon handles http urls directly without needing httpx when used as file
                # But we download it to use as video thumb if needed, and to send as guaranteed photo
                async with httpx.AsyncClient(timeout=30) as http_client:
                    resp = await http_client.get(poster_url)
                    if resp.status_code == 200:
                        thumb_path = os.path.join(tempfile.gettempdir(), f"thumb_{title[:20].replace(' ','_')}.jpg")
                        with open(thumb_path, "wb") as pf:
                            pf.write(resp.content)
            except Exception as e:
                logger.warning(f"Failed to download poster for thumbnail: {e}")
                thumb_path = None
        
        # 4. First send the poster with the caption
        # Make sure we don't try to send an empty file path or url
        file_to_send = thumb_path if thumb_path else poster_url.strip() if poster_url else None
        
        if file_to_send:
            await client.send_file(
                chat_id,
                file_to_send,
                caption=caption,
                parse_mode='md',
                force_document=False,
                reply_to=message_thread_id
            )
        else:
            # If no poster available at all, just send the caption as text
            await client.send_message(
                chat_id,
                caption,
                parse_mode='md',
                reply_to=message_thread_id
            )
        
        status_msg = await client.send_message(
            chat_id, 
            "📤 Sedang mengupload final video ke Telegram...",
            reply_to=message_thread_id
        )
        
        video_attributes = [
            DocumentAttributeVideo(
                duration=duration,
                w=width,
                h=height,
                supports_streaming=True
            )
        ]
        
        # 5. Then upload final video with small caption
        await client.send_file(
            chat_id,
            video_path,
            caption=f"🎥 Full Episode: **{title}**",
            thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
            attributes=video_attributes,
            progress_callback=lambda c, t: upload_progress(c, t, status_msg, "Upload Video:"),
            supports_streaming=True,
            reply_to=message_thread_id
        )
        
        await status_msg.delete()
        
        # 6. Cleanup
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        logger.info(f"Successfully uploaded final video {title} to Telegram")
        return True
    except Exception as e:
        logger.error(f"Failed to upload to Telegram: {e}")
        return False
