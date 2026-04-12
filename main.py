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
    search_dramas
)
from downloader import download_all_episodes
from merge import merge_episodes
from uploader import upload_drama
from db import init_db, add_to_queue

# Configuration
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
AUTO_CHANNEL = int(os.environ.get("AUTO_CHANNEL", ADMIN_ID))
MESSAGE_THREAD_ID = int(os.environ.get("MESSAGE_THREAD_ID", "0")) or None
PROCESSED_FILE = "processed.json"

# Initialize state
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
client = TelegramClient('dramabox_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_panel_buttons():
    status_text = "🟢 RUNNING" if BotState.is_auto_running else "🔴 STOPPED"
    return [
        [Button.inline("▶️ Start Auto", b"start_auto"), Button.inline("⏹ Stop Auto", b"stop_auto")],
        [Button.inline(f"📊 Status: {status_text}", b"status")]
    ]

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
        
        # Restart the script forcefully
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await status_msg.edit(f"❌ Gagal melakukan update: {e}")

@client.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.chat_id != ADMIN_ID:
        return
    BotState.is_auto_running = False
    await event.reply("🎛 **Dramabox Control Panel**\n\nAuto-mode has been **Stopped**. Use the buttons below to control.", buttons=get_panel_buttons())

@client.on(events.CallbackQuery())
async def panel_callback(event):
    if event.sender_id != ADMIN_ID:
        return
        
    data = event.data
    
    try:
        if data == b"start_auto":
            BotState.is_auto_running = True
            await event.answer("Auto-mode started!")
            await event.edit("🎛 **Dramabox Control Panel**", buttons=get_panel_buttons())
        elif data == b"stop_auto":
            BotState.is_auto_running = False
            await event.answer("Auto-mode stopped!")
            await event.edit("🎛 **Dramabox Control Panel**", buttons=get_panel_buttons())
        elif data == b"status":
            await event.answer(f"Status: {'Running' if BotState.is_auto_running else 'Stopped'}")
            await event.edit("🎛 **Dramabox Control Panel**", buttons=get_panel_buttons())
    except Exception as e:
        if "message is not modified" in str(e).lower() or "Message string and reply markup" in str(e):
            pass 
        else:
            logger.error(f"Callback error: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Welcome to Dramabox Downloader Bot! 🎉\n\nGunakan perintah `/download {bookId}` atau `/cari {judul}` untuk mulai.")

@client.on(events.NewMessage(pattern=r'/cari (.+)'))
async def on_search(event):
    if event.chat_id != ADMIN_ID:
        return
        
    keyword = event.pattern_match.group(1).strip()
    status_msg = await event.reply(f"🔍 Mencari `{keyword}`...")
    
    results = await search_dramas(keyword, pages=1)
    
    if not results:
        await status_msg.edit(f"❌ Tidak ditemukan hasil untuk `{keyword}`.")
        return
        
    text = f"**Hasil Pencarian untuk:** `{keyword}`\n\n"
    for idx, d in enumerate(results[:15], 1):
        book_id = str(d.get("bookId") or d.get("id") or d.get("bookid", ""))
        title = d.get("title") or d.get("bookName") or d.get("name") or "Unknown"
        status = "✅" if book_id in processed_ids else "☑️"
        text += f"{idx}. {status} **{title}**\n   └ ID: `{book_id}`\n"
        
    text += "\nKeterangan: ✅ Sudah di-download | ☑️ Belum\n"
    text += "\nGunakan `/download <ID>` untuk mengunduh."
    
    await status_msg.edit(text)

@client.on(events.NewMessage(func=lambda e: e.video))
async def on_video_upload(event):
    if event.chat_id != ADMIN_ID:
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
    
    if chat_id != ADMIN_ID:
        await event.reply("❌ Maaf, perintah ini hanya untuk admin.")
        return
        
    if BotState.is_processing:
        await event.reply("⚠️ Sedang memproses drama lain. Tunggu hingga selesai (Anti bentrok).")
        return
        
    book_id = event.pattern_match.group(1)
    
    detail = await get_drama_detail(book_id)
    if not detail:
        await event.reply(f"❌ Gagal mendapatkan detail drama `{book_id}`.")
        return
        
    episodes = await get_all_episodes(book_id)
    if not episodes:
        await event.reply(f"❌ Drama `{book_id}` tidak memiliki episode.")
        return
    title = detail.get("title") or detail.get("bookName") or detail.get("name") or f"Drama_{book_id}"
    
    status_msg = await event.reply(f"🎬 Drama: **{title}**\n📽 Total Episodes: {len(episodes)}\n\n⏳ Sedang mendownload dan memproses...")
    
    BotState.is_processing = True
    processed_ids.add(book_id)
    save_processed(processed_ids)
    
    await process_drama_full(book_id, chat_id, status_msg)
    BotState.is_processing = False

async def process_drama_full(book_id, chat_id, status_msg=None, message_thread_id=None):
    """Processes a drama from GoodShort API."""
    detail = await get_drama_detail(book_id)
    episodes = await get_all_episodes(book_id)
    
    if not detail or not episodes:
        error_msg = f"❌ Detail atau Episode `{book_id}` tidak ditemukan."
        if status_msg: await status_msg.edit(error_msg)
        return False, error_msg

    title = detail.get("title") or detail.get("bookName") or detail.get("name") or f"Drama_{book_id}"
    description = detail.get("intro") or detail.get("introduction") or detail.get("description") or "No description available."
    poster = detail.get("cover") or detail.get("coverWap") or detail.get("poster") or ""
    
    temp_dir = tempfile.mkdtemp(prefix=f"dramabox_{book_id}_")
    video_dir = os.path.join(temp_dir, "episodes")
    os.makedirs(video_dir, exist_ok=True)
    
    try:
        if status_msg: await status_msg.edit(f"🎬 Processing **{title}**...")
        
        success = await download_all_episodes(episodes, video_dir)
        if not success:
            error_text = f"❌ Gagal Download episode drama **{title}**."
            if status_msg: await status_msg.edit(error_text)
            return False, error_text

        output_video_path = os.path.join(temp_dir, f"{title}.mp4")
        merge_success = merge_episodes(video_dir, output_video_path)
        if not merge_success:
            error_text = f"❌ Gagal Merge video drama **{title}**."
            if status_msg: await status_msg.edit(error_text)
            return False, error_text

        upload_success = await upload_drama(
            client, chat_id, 
            title, description, 
            poster, output_video_path,
            total_episodes=len(episodes),
            message_thread_id=message_thread_id
        )
        
        if upload_success:
            if status_msg: await status_msg.delete()
            return True, "Sukses"
        else:
            error_text = f"❌ Gagal Upload video drama **{title}** ke Telegram."
            if status_msg: await status_msg.edit(error_text)
            return False, error_text
            
    except Exception as e:
        err_msg = f"❌ Error Sistem pada **{title}**: {str(e)}"
        logger.error(f"Error processing {book_id}: {e}")
        if status_msg: await status_msg.edit(err_msg)
        return False, err_msg
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def auto_mode_loop():
    """Loop to find and process new dramas automatically using GoodShort API."""
    global processed_ids
    
    logger.info("🚀 Full Auto-Mode Started.")
    is_initial_run = True
    
    while True:
        if not BotState.is_auto_running:
            await asyncio.sleep(5)
            continue
            
        try:
            interval = 5 if is_initial_run else 15
            logger.info(f"🔍 Scanning for new dramas (Next scan in {interval}m)...")
            
            api_new = []
            channels = [-1, 563, 656, 567] # Tren, Terbaru, Anime, Dubing
            
            for chan_id in channels:
                scan_pages = 20 if is_initial_run else 2
                chan_dramas = await get_latest_dramas(pages=scan_pages, channel=chan_id) or []
                for d in reversed(chan_dramas):
                    book_id = str(d.get("bookId") or d.get("id") or d.get("bookid", ""))
                    if book_id and book_id not in processed_ids:
                        if d not in api_new:
                            api_new.append(d)
            
            if not api_new and not is_initial_run:
                logger.info("ℹ️ GoodShort is up to date. Fetching fallback from Page 1...")
                # Try Tren (Channel -1) Page 1 as fallback
                fallback_dramas = await get_latest_dramas(pages=1, channel=-1) or []
                fallback_new = [d for d in fallback_dramas if str(d.get("bookId") or d.get("id") or d.get("bookid", "")) not in processed_ids]
                
                if fallback_new:
                    random_drama = random.choice(fallback_new)
                    api_new = [random_drama]
                    logger.info(f"🎲 Fallback picked: {random_drama.get('title')}")
                else:
                    # Try Popular Search if Page 1 is also fully processed
                    pop_dramas = await get_latest_dramas(pages=1, types=["populersearch"]) or []
                    pop_new = [d for d in pop_dramas if str(d.get("bookId") or d.get("id") or d.get("bookid", "")) not in processed_ids]
                    if pop_new:
                        api_new = [random.choice(pop_new)]
                    else:
                        logger.info("😴 No new dramas found even in fallback.")

            new_found = 0
            for drama in api_new:
                if not BotState.is_auto_running:
                    break
                    
                book_id = str(drama.get("bookId") or drama.get("id") or drama.get("bookid", ""))
                if not book_id or book_id in processed_ids:
                    continue
                    
                processed_ids.add(book_id)
                save_processed(processed_ids)
                
                new_found += 1
                title = drama.get("title") or drama.get("bookName") or drama.get("name") or "Unknown"
                logger.info(f"✨ New drama detected: {title} ({book_id}). Starting process...")
                
                try:
                    await client.send_message(ADMIN_ID, f"🆕 **Auto-System Mendeteksi Drama Baru!**\n🎬 `{title}`\n🆔 `{book_id}`\n⏳ Memproses download & merge...")
                except: pass
                
                BotState.is_processing = True
                success, reason = await process_drama_full(book_id, AUTO_CHANNEL, message_thread_id=MESSAGE_THREAD_ID)
                BotState.is_processing = False
                
                if success:
                    logger.info(f"✅ Finished {title}")
                    try:
                        await client.send_message(ADMIN_ID, f"✅ Sukses Auto-Post: **{title}** ke channel.")
                    except: pass
                else:
                    logger.error(f"❌ Failed to process {title}: {reason}")
                    try:
                        await client.send_message(ADMIN_ID, f"⚠️ **Gagal Auto-Post `{title}`**\n\n📌 Alasan: {reason}")
                    except: pass
                
                await asyncio.sleep(10)
            
            if new_found == 0:
                logger.info("😴 No new dramas found.")
            
            is_initial_run = False
            for _ in range(interval * 60):
                if not BotState.is_auto_running:
                    break
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"⚠️ Error in auto_mode_loop: {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    logger.info("Initializing Dramabox Auto-Bot...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    client.loop.create_task(auto_mode_loop())
    logger.info("Bot is active and monitoring.")
    client.run_until_disconnected()
