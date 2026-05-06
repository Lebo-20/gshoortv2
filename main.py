import os
import asyncio
import logging
import shutil
import tempfile
import random
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv

load_dotenv()

# Local imports
from api import (
    get_drama_detail, get_all_episodes, get_latest_dramas,
    get_home_dramas, search_dramas
)
from downloader import download_all_episodes
from merge import merge_episodes
from uploader import upload_drama

# Configuration
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
AUTO_CHANNEL = int(os.environ.get("AUTO_CHANNEL", ADMIN_ID))
PROCESSED_FILE = "processed.json"
FAILURES_FILE = "failures.json"
TARGET_CHANNEL = -1003857149032 # From 3857149032
TARGET_TOPIC = 39

# Progress Bar Utility
def get_progress_bar(percentage, length=15):
    filled_length = int(length * percentage / 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"|{bar}| {percentage:.1f}%"

# Failure Management
def load_failures():
    if os.path.exists(FAILURES_FILE):
        import json
        with open(FAILURES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_failures(data):
    import json
    with open(FAILURES_FILE, "w") as f:
        json.dump(data, f)

failures = load_failures()

def should_skip(book_id):
    import time
    entry = failures.get(book_id)
    if entry and entry.get("count", 0) >= 2:
        last_fail = entry.get("time", 0)
        # Skip for 1 day (86400 seconds)
        if time.time() - last_fail < 86400:
            return True
    return False

def record_failure(book_id):
    import time
    entry = failures.get(book_id, {"count": 0, "time": 0})
    entry["count"] += 1
    entry["time"] = time.time()
    failures[book_id] = entry
    save_failures(failures)

def reset_failure(book_id):
    if book_id in failures:
        del failures[book_id]
        save_failures(failures)

# State Management
def load_processed():
    if os.path.exists(PROCESSED_FILE):
        import json
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_processed(data):
    import json
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(data), f)

processed_ids = load_processed()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Bot State
class BotState:
    is_auto_running = True
    is_processing = False

# Initialize client
client = TelegramClient('goodshort_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_panel_buttons():
    status_text = "🟢 RUNNING" if BotState.is_auto_running else "🔴 STOPPED"
    return [
        [Button.inline("▶️ Start Auto", b"start_auto"), Button.inline("⏹ Stop Auto", b"stop_auto")],
        [Button.inline(f"📊 Status: {status_text}", b"status")]
    ]

# ... Panel handlers are ok ...
@client.on(events.NewMessage(pattern='/update'))
async def update_bot(event):
    if event.sender_id != ADMIN_ID:
        return
    import subprocess
    import sys
    
    status_msg = await event.reply("🔄 Menarik pembaruan dari GitHub...")
    try:
        # Run git pull
        result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
        await status_msg.edit(f"✅ Repositori berhasil di-pull:\n```\n{result.stdout}\n```\n\nSedang memulai ulang sistem (Restarting)...")
        
        # Free session lock before restarting
        await client.disconnect()
        
        # Restart the script
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await status_msg.edit(f"❌ Gagal melakukan update: {e}")

@client.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID:
        return
    await event.reply("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())

@client.on(events.CallbackQuery())
async def panel_callback(event):
    if event.sender_id != ADMIN_ID:
        return
    data = event.data
    try:
        if data == b"start_auto":
            BotState.is_auto_running = True
            await event.answer("Auto-mode started!")
            await event.edit("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())
        elif data == b"stop_auto":
            BotState.is_auto_running = False
            await event.answer("Auto-mode stopped!")
            await event.edit("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())
        elif data == b"status":
            await event.answer(f"Status: {'Running' if BotState.is_auto_running else 'Stopped'}")
            await event.edit("🎛 **DramaBite Control Panel**", buttons=get_panel_buttons())
    except Exception as e:
        if "message is not modified" in str(e).lower() or "Message string and reply markup" in str(e):
            pass
        else:
            logger.error(f"Callback error: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Welcome to GoodShort Downloader Bot! 🎉\n\nGunakan perintah `/download {bookId}` atau `/cari {judul}` untuk mulai.")

@client.on(events.NewMessage(pattern=r'/cari (.+)'))
async def on_search(event):
    if event.sender_id != ADMIN_ID:
        return
        
    keyword = event.pattern_match.group(1).strip()
    status_msg = await event.reply(f"🔍 Mencari `{keyword}`...")
    
    results = await search_dramas(keyword)
    
    if not results:
        await status_msg.edit(f"❌ Tidak ditemukan hasil untuk `{keyword}`.")
        return
        
    text = f"**Hasil Pencarian untuk:** `{keyword}`\n\n"
    for idx, d in enumerate(results[:15], 1):
        book_id = str(d.get("cid") or d.get("id") or "")
        title = d.get("title") or d.get("name") or "Unknown"
        status = "✅" if book_id in processed_ids else "☑️"
        text += f"{idx}. {status} **{title}**\n   └ ID: `{book_id}`\n"
        
    text += "\nKeterangan: ✅ Sudah di-download | ☑️ Belum\n"
    text += "\nGunakan `/download <ID>` untuk mengunduh."
    
    await status_msg.edit(text)

@client.on(events.NewMessage(func=lambda e: e.video))
async def on_video_upload(event):
    if event.sender_id != ADMIN_ID:
        return

    video = event.video
    file_id = f"{video.id}_{video.access_hash}"
    file_name = event.file.name or f"video_{video.id}.mp4"
    user_id = str(event.sender_id)

    success = await add_to_queue(user_id, file_id, file_name)
    
    if success:
        await event.reply(f"📥 **Video ditambahkan ke antrian**\n📄 `{file_name}`")
    else:
        await event.reply("⚠️ **Video sudah ada di database** (Duplicate skipped)")

@client.on(events.NewMessage(pattern=r'/download (\d+)'))
async def on_download(event):
    chat_id = event.chat_id
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Maaf, perintah ini hanya untuk admin.")
        return
    if BotState.is_processing:
        await event.reply("⚠️ Sedang memproses drama lain. Tunggu hingga selesai.")
        return
    book_id = event.pattern_match.group(1)
    
    # Check detail
    detail = await get_drama_detail(book_id)
    if not detail:
        await event.reply(f"❌ Gagal mendapatkan detail drama `{book_id}`.")
        return
        
    episodes = await get_all_episodes(book_id)
    if not episodes:
        await event.reply(f"❌ Drama `{book_id}` tidak memiliki episode.")
        return
        
    title = detail.get("title") or detail.get("name") or f"Drama_{book_id}"
    status_msg = await event.reply(f"🎬 Drama: **{title}**\n📽 Total Episodes: {len(episodes)}\n\n⏳ Sedang mendownload...")
    
    BotState.is_processing = True
    # Set thread ID correctly if triggered in a topic
    thread_id = None
    if event.is_reply:
        thread_id = event.message.reply_to_msg_id
    elif getattr(event.message, 'reply_to', None) and getattr(event.message.reply_to, 'reply_to_top_id', None):
        thread_id = event.message.reply_to.reply_to_top_id
    elif getattr(event.message, 'reply_to', None) and getattr(event.message.reply_to, 'reply_to_msg_id', None):
        thread_id = event.message.reply_to.reply_to_msg_id
    elif chat_id == AUTO_CHANNEL:
        thread_id = MESSAGE_THREAD_ID
        
    await process_drama_full(book_id, chat_id, status_msg, message_thread_id=thread_id)
    BotState.is_processing = False

async def process_drama_full(book_id, chat_id, status_msg=None, reply_to=None):
    """DramaBite specific processing logic with detailed progress."""
    if should_skip(book_id):
        logger.info(f"⏭ Skipping {book_id} due to previous failures.")
        return False

    detail = await get_drama_detail(book_id)
    episodes = await get_all_episodes(book_id)
    
    if not detail or not episodes:
        if status_msg: await status_msg.edit(f"❌ Detail atau Episode `{book_id}` tidak ditemukan.")
        record_failure(book_id)
        return False

    title = detail.get("title") or detail.get("name") or f"Drama_{book_id}"
    description = detail.get("desc") or detail.get("description") or "No description available."
    poster = detail.get("cover") or detail.get("poster") or ""
    
    temp_dir = tempfile.mkdtemp(prefix=f"dramabite_{book_id}_")
    video_dir = os.path.join(temp_dir, "episodes")
    os.makedirs(video_dir, exist_ok=True)
    
    try:
        import time
        start_proc = time.time()
        
        if not status_msg:
            status_msg = await client.send_message(chat_id, f"🎬 **Memulai Proses:** `{title}`", reply_to=reply_to)
        else:
            await status_msg.edit(f"🎬 **Memulai Proses:** `{title}`")
        
        # Download Callback
        async def dl_progress(current, total):
            pct = (current / total) * 100
            bar = get_progress_bar(pct)
            try:
                await status_msg.edit(f"🎬 **{title}**\n📥 **Downloading Episodes...**\n{bar}\n📦 {current}/{total} Episodes")
            except: pass

        # Download - Passing book_id to downloader
        success = await download_all_episodes(episodes, video_dir, book_id=book_id, progress_callback=dl_progress)
        if not success:
            await status_msg.edit(f"❌ **Download Gagal:** `{title}`")
            record_failure(book_id)
            return False

        # Merge
        await status_msg.edit(f"🎬 **{title}**\n🔄 **Merging episodes...** Mohon tunggu.")
        output_video_path = os.path.join(temp_dir, f"{title}.mp4")
        merge_success = merge_episodes(video_dir, output_video_path)
        if not merge_success:
            await status_msg.edit(f"❌ **Merge Gagal:** `{title}`")
            record_failure(book_id)
            return False

        # Upload
        upload_success = await upload_drama(
            client, chat_id, title, description, poster, output_video_path, reply_to=reply_to
        )
        
        if upload_success:
            await status_msg.delete()
            reset_failure(book_id)
            return True
        else:
            await status_msg.edit(f"❌ **Upload Gagal:** `{title}`")
            record_failure(book_id)
            return False
    except Exception as e:
        logger.error(f"Error processing {book_id}: {e}")
        if status_msg: await status_msg.edit(f"❌ **Error:** {e}")
        record_failure(book_id)
        return False
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def auto_mode_loop():
    """Loop to find and process new dramas from GoodShort."""
    global processed_ids
    logger.info("🚀 GoodShort Auto-Mode Started.")
    is_initial_run = True
    
    while True:
        if not BotState.is_auto_running:
            await asyncio.sleep(5)
            continue
            
        try:
            interval = 5 if is_initial_run else 15
            logger.info(f"🔍 Scanning sources (Next in {interval}m)...")
            
            # Source 1: Recommendation (Module)
            rec_dramas = await get_latest_dramas(pages=50 if is_initial_run else 1) or []
            
            # Source 2: Home Page
            home_dramas = await get_home_dramas() or []
            
            # Combine
            new_queue = []
            seen_in_scan = set()
            for d in (rec_dramas + home_dramas):
                if not isinstance(d, dict):
                    continue
                book_id = str(d.get("cid") or d.get("id") or "")
                if not book_id or book_id in seen_in_scan or should_skip(book_id):
                    continue
                seen_in_scan.add(book_id)
                if book_id not in processed_ids:
                    new_queue.append(d)
            
            new_queue.reverse() # Oldest first
            
            for drama in new_queue:
                if not BotState.is_auto_running: break
                    
                book_id = str(drama.get("cid") or drama.get("id"))
                title = drama.get("title") or "Unknown"
                
                processed_ids.add(book_id)
                save_processed(processed_ids)
                
                logger.info(f"✨ New discovery: {title} ({book_id})")
                
                BotState.is_processing = True
                # Process in the TARGET TOPIC
                success = await process_drama_full(book_id, TARGET_CHANNEL, reply_to=TARGET_TOPIC)
                BotState.is_processing = False
                
                if success:
                    logger.info(f"✅ Finished {title}")
                    try:
                        await client.send_message(ADMIN_ID, f"✅ **Sukses Auto-Post:** `{title}`\n⏳ Jeda: 1 jam.")
                    except: pass
                    await asyncio.sleep(3600) # 1 hour delay after success
                else:
                    logger.error(f"❌ Failed to process {title}")
                    try:
                        await client.send_message(ADMIN_ID, f"🚨 **ERROR**: Proses `{title}` gagal!")
                    except: pass
                    await asyncio.sleep(10)
            
            is_initial_run = False
            for _ in range(interval * 60):
                if not BotState.is_auto_running: break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"⚠️ Loop error: {e}")
            await asyncio.sleep(60)
            
            is_initial_run = False
            for _ in range(interval * 60):
                if not BotState.is_auto_running: break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"⚠️ Loop error: {e}")
            await asyncio.sleep(60)


if __name__ == '__main__':
    logger.info("Initializing GoodShort Auto-Bot...")
    
    # Start auto loop and keep the client running
    client.loop.create_task(auto_mode_loop())
    
    logger.info("Bot is active and monitoring.")
    client.run_until_disconnected()
