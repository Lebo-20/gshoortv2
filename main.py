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
TARGET_TOPIC = 1795

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
    if not entry:
        return False
        
    count = entry.get("count", 0)
    last_fail = entry.get("time", 0)
    
    # If 3 or more failures, skip permanently
    if count >= 3:
        return True
        
    # If 1 or 2 failures, skip for 1 day (86400 seconds)
    if count >= 1:
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

PROCESSED_TITLES_FILE = "processed_titles.json"

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        import json
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def load_processed_titles():
    if os.path.exists(PROCESSED_TITLES_FILE):
        import json
        with open(PROCESSED_TITLES_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_processed(ids, titles):
    import json
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(ids), f)
    with open(PROCESSED_TITLES_FILE, "w") as f:
        json.dump(list(titles), f)

processed_ids = load_processed()
processed_titles = load_processed_titles()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Bot State
class BotState:
    is_auto_running = True
    is_processing = False
    lock = asyncio.Lock()
    manual_queue = asyncio.Queue() # Queue for manual requests
    user_states = {} # Track user interaction states

# Initialize client
client = TelegramClient('goodshort_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_panel_buttons():
    status_text = "🟢 RUNNING" if BotState.is_auto_running else "🔴 STOPPED"
    return [
        [Button.inline("▶️ Start Auto", b"start_auto"), Button.inline("⏹ Stop Auto", b"stop_auto")],
        [Button.inline(f"📊 Panel Status: {status_text}", b"status")],
        [Button.inline("🔄 Update via GitHub", b"admin_update")]
    ]

def get_main_menu():
    return [
        [Button.inline("🔍 Cari Drama", b"menu_search"), Button.inline("📥 Download via ID", b"menu_download")],
        [Button.inline("ℹ️ Status & Info", b"menu_status")]
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

async def check_proxy_status():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get("http://localhost:3100/status")
            if response.status_code == 200:
                return "🟢 Online"
    except:
        pass
    return "🔴 Offline"

@client.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID:
        return
    await event.reply("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())

async def perform_update(event):
    import subprocess
    import sys
    
    msg = await event.respond("🔄 **Memulai Pembaruan...**")
    try:
        # Run git pull
        result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
        await msg.edit(f"✅ **Update Berhasil!**\n\n```\n{result.stdout}\n```\n\n🔄 Sedang memulai ulang sistem...")
        
        # Free session lock
        await client.disconnect()
        # Restart
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await msg.edit(f"❌ **Gagal Update:** {e}")

@client.on(events.CallbackQuery())
async def on_callback(event):
    data = event.data
    user_id = event.sender_id
    
    try:
        # Admin Panel Logic
        if user_id == ADMIN_ID:
            if data == b"start_auto":
                BotState.is_auto_running = True
                await event.answer("Auto-mode started!")
                await event.edit("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())
                return
            elif data == b"stop_auto":
                BotState.is_auto_running = False
                await event.answer("Auto-mode stopped!")
                await event.edit("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())
                return
            elif data == b"status":
                await event.answer(f"Status: {'Running' if BotState.is_auto_running else 'Stopped'}")
                await event.edit("🎛 **GoodShort Control Panel**", buttons=get_panel_buttons())
                return
            elif data == b"admin_update":
                await event.answer("Updating system...")
                await perform_update(event)
                return

        # Main Menu Logic (For Everyone)
        if data == b"menu_search":
            BotState.user_states[user_id] = "waiting_search"
            await event.edit("🔍 **Pencarian Drama**\n\nSilakan kirimkan **Judul Drama** yang ingin Anda cari (Contoh: `Suamiku Bos Besar`).", buttons=[Button.inline("🔙 Kembali", b"menu_back")])
        
        elif data == b"menu_download":
            BotState.user_states[user_id] = "waiting_download"
            await event.edit("📥 **Download via ID**\n\nSilakan kirimkan **Book ID** drama yang ingin didownload.\n\n_Tips: Gunakan menu Cari jika belum tahu ID-nya._", buttons=[Button.inline("🔙 Kembali", b"menu_back")])
            
        elif data == b"menu_status":
            q_size = BotState.manual_queue.qsize()
            status = "🟢 Aktif" if BotState.is_auto_running else "🔴 Standby"
            proc = "⏳ Sedang Download" if BotState.is_processing else "✅ Idle"
            proxy_status = await check_proxy_status()
            
            text = (
                "ℹ️ **Bot Information**\n\n"
                f"📡 Bot Status: **{status}**\n"
                f"🌐 Proxy Status: **{proxy_status}**\n"
                f"⚙️ Worker: **{proc}**\n"
                f"📦 Antrian: **{q_size} drama**\n"
            )
            await event.edit(text, buttons=[Button.inline("🔙 Kembali", b"menu_back")])
            
        elif data == b"menu_back":
            BotState.user_states.pop(user_id, None)
            await event.edit("🎬 **GoodShort Downloader Menu**\n\nSilakan pilih layanan di bawah ini:", buttons=get_main_menu())

        # Detail Drama Logic
        elif data.startswith(b"det_"):
            book_id = data.decode().split("_")[1]
            await show_drama_detail(event, book_id)

        # Back to Search Results
        elif data.startswith(b"back_search_"):
            keyword = data.decode().split("_", 2)[2]
            await perform_search_inline(event, keyword)

        # Direct Download from Detail
        elif data.startswith(b"dl_"):
            book_id = data.decode().split("_")[1]
            await event.answer("📥 Menambahkan ke antrian download...")
            await handle_download_logic(book_id, event.chat_id, event)

    except Exception as e:
        if "message is not modified" in str(e).lower(): pass
        else: logger.error(f"Callback error: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    BotState.user_states.pop(user_id, None)
    await event.reply(
        "🎬 **Selamat Datang di GoodShort Downloader!**\n\n"
        "Saya adalah bot otomatis untuk mendownload drama dari GoodShort. "
        "Silakan pilih menu di bawah ini untuk memulai.",
        buttons=get_main_menu()
    )

@client.on(events.NewMessage())
async def on_user_input(event):
    # Only handle messages that are NOT commands
    if event.text.startswith('/'):
        return
        
    user_id = event.sender_id
    state = BotState.user_states.get(user_id)
    
    if state == "waiting_search":
        keyword = event.text.strip()
        await event.delete()
        await perform_search_inline(event, keyword)
        BotState.user_states.pop(user_id, None)

    elif state == "waiting_download":
        await event.delete()
        book_id = event.text.strip()
        if not book_id.isdigit():
            await event.respond("❌ ID harus berupa angka.", buttons=[Button.inline("🔙 Kembali", b"menu_back")])
            return
            
        BotState.user_states.pop(user_id, None)
        # Re-use the existing download logic by creating a fake event-like structure or just calling the logic
        await handle_download_logic(book_id, event.chat_id, event)

@client.on(events.NewMessage(pattern=r'/cari (.+)'))
async def on_search_cmd(event):
    keyword = event.pattern_match.group(1).strip()
    status_msg = await event.reply(f"🔍 Mencari `{keyword}`...")
    # ... rest of logic ... (I'll keep it for compatibility but redirect to a helper)
    await perform_search(keyword, status_msg)

async def perform_search_inline(event, keyword):
    """Helper to show search results as buttons"""
    results = await search_dramas(keyword)
    if not results:
        msg = f"❌ Tidak ditemukan hasil untuk `{keyword}`."
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(msg, buttons=[Button.inline("🔙 Kembali", b"menu_back")])
        else:
            await event.respond(msg, buttons=[Button.inline("🔙 Kembali", b"menu_back")])
        return

    buttons = []
    for d in results[:12]: # Limit 12 results for button clarity
        book_id = str(d.get("bookId") or d.get("cid") or d.get("id") or "")
        title = d.get("bookName") or d.get("title") or d.get("name") or "Unknown"
        status = "✅" if book_id in processed_ids else "🎬"
        buttons.append([Button.inline(f"{status} {title}", f"det_{book_id}".encode())])
    
    buttons.append([Button.inline("🔙 Kembali ke Menu", b"menu_back")])
    
    text = f"🔍 **Hasil Pencarian untuk:** `{keyword}`\n\nSilakan klik pada judul drama untuk melihat detail dan sinopsis."
    
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

async def show_drama_detail(event, book_id):
    """Show drama poster, synopsis and download button"""
    try:
        detail = await get_drama_detail(book_id)
        if not detail:
            await event.answer("❌ Gagal mengambil detail drama.", alert=True)
            return

        book_info = detail.get("book") if isinstance(detail.get("book"), dict) else detail
        title = book_info.get("bookName") or book_info.get("title") or "Unknown Title"
        description = book_info.get("introduction") or book_info.get("desc") or "Tidak ada sinopsis."
        poster = book_info.get("cover") or book_info.get("poster")
        
        # Clean up description if too long
        if len(description) > 800:
            description = description[:800] + "..."

        caption = (
            f"🎬 **{title}**\n\n"
            f"📝 **Sinopsis:**\n{description}\n\n"
            f"🆔 ID: `{book_id}`"
        )
        
        buttons = [
            [Button.inline("📥 Download Sekarang", f"dl_{book_id}".encode())],
            [Button.inline("🔙 Kembali ke Hasil", f"back_search_{title[:20]}".encode())],
            [Button.inline("🏠 Menu Utama", b"menu_back")]
        ]

        if poster:
            # Delete previous message and send new one with photo
            await event.delete()
            await client.send_file(event.chat_id, poster, caption=caption, buttons=buttons)
        else:
            await event.edit(caption, buttons=buttons)
            
    except Exception as e:
        logger.error(f"Error showing detail: {e}")
        await event.answer("❌ Terjadi kesalahan saat memuat detail.", alert=True)

async def perform_search(keyword, msg):
    # This is for the /cari command compatibility
    await perform_search_inline(msg, keyword)

@client.on(events.NewMessage(pattern=r'/download (\d+)'))
async def on_download_cmd(event):
    book_id = event.pattern_match.group(1)
    await handle_download_logic(book_id, event.chat_id, event)

async def handle_download_logic(book_id, chat_id, event):
    if BotState.lock.locked():
        await event.respond("⏳ **Antrian:** Bot sedang sibuk. Permintaan Anda telah dimasukkan ke antrian.")
    
    # Add to manual queue
    await BotState.manual_queue.put((book_id, chat_id, event))

@client.on(events.NewMessage(func=lambda e: e.video))
async def on_video_upload(event):
    if event.sender_id != ADMIN_ID:
        return

    video = event.video
    file_id = f"{video.id}_{video.access_hash}"
    file_name = event.file.name or f"video_{video.id}.mp4"
    await event.reply(f"📥 **Video Terdeteksi**\n📄 `{file_name}`\n\n_Gunakan menu atau ID untuk mendownload drama._")

async def manual_worker():
    """Background worker to process manual download requests."""
    logger.info("👷 Manual Worker Started.")
    while True:
        book_id, chat_id, event = await BotState.manual_queue.get()
        
        async with BotState.lock:
            BotState.is_processing = True
            try:
                # Check detail
                detail = await get_drama_detail(book_id)
                if not detail:
                    await event.reply(f"❌ Gagal mendapatkan detail drama `{book_id}`.")
                    continue
                    
                episodes = await get_all_episodes(book_id)
                if not episodes:
                    await event.reply(f"❌ Drama `{book_id}` tidak memiliki episode.")
                    continue
                    
                book_info = detail.get("book") if isinstance(detail.get("book"), dict) else detail
                title = book_info.get("bookName") or book_info.get("title") or book_info.get("name") or f"Drama_{book_id}"
                
                status_msg = await event.reply(f"🚀 **Manual Download Started!**\n🎬 Drama: **{title}**\n\n⏳ Mohon tunggu...")
                
                # Set thread ID
                thread_id = None
                if event.is_reply:
                    thread_id = event.message.reply_to_msg_id
                elif getattr(event.message, 'reply_to', None) and getattr(event.message.reply_to, 'reply_to_top_id', None):
                    thread_id = event.message.reply_to.reply_to_top_id
                
                await process_drama_full(book_id, chat_id, status_msg, reply_to=thread_id)
            except Exception as e:
                logger.error(f"Error in manual worker: {e}")
                try: await event.reply(f"❌ **Error Manual Download:** {e}")
                except: pass
            finally:
                BotState.is_processing = False
                BotState.manual_queue.task_done()

async def process_drama_full(book_id, chat_id, status_msg=None, reply_to=None):
    """GoodShort specific processing logic with detailed progress."""
    if should_skip(book_id):
        logger.info(f"⏭ Skipping {book_id} due to previous failures.")
        return False

    detail = await get_drama_detail(book_id)
    episodes = await get_all_episodes(book_id)
    
    if not detail or not episodes:
        if status_msg: await status_msg.edit(f"❌ Detail atau Episode `{book_id}` tidak ditemukan.")
        record_failure(book_id)
        return False

    book_info = detail.get("book") if isinstance(detail.get("book"), dict) else detail
    title = book_info.get("bookName") or book_info.get("title") or book_info.get("name") or f"Drama_{book_id}"
    description = book_info.get("introduction") or book_info.get("desc") or book_info.get("description") or "No description available."
    poster = book_info.get("cover") or book_info.get("poster") or ""
    
    temp_dir = tempfile.mkdtemp(prefix=f"goodshort_{book_id}_")
    video_dir = os.path.join(temp_dir, "episodes")
    os.makedirs(video_dir, exist_ok=True)
    
    try:
        import time
        start_proc = time.time()
        
        if not status_msg:
            status_msg = await client.send_message(chat_id, f"🎬 **Memulai Proses:** `{title}`", reply_to=reply_to)
        else:
            await status_msg.edit(f"🎬 **Memulai Proses:** `{title}`")
        
        # Download Callback with Throttling to prevent Flood Wait
        last_update_time = 0
        async def dl_progress(current, total):
            nonlocal last_update_time
            import time
            now = time.time()
            # Update only every 5 seconds or when finished
            if now - last_update_time < 5 and current < total:
                return
            
            last_update_time = now
            pct = (current / total) * 100
            bar = get_progress_bar(pct)
            try:
                await status_msg.edit(f"🎬 **{title}**\n📥 **Downloading Episodes...**\n{bar}\n📦 {current}/{total} Episodes")
            except Exception as e:
                if "flood" in str(e).lower():
                    pass # Silently ignore flood errors during progress

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
            processed_ids.add(book_id)
            processed_titles.add(title.strip().lower())
            save_processed(processed_ids, processed_titles)
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
                book_id = str(d.get("bookId") or d.get("cid") or d.get("id") or "")
                if not book_id or book_id in seen_in_scan or should_skip(book_id):
                    continue
                seen_in_scan.add(book_id)
                if book_id not in processed_ids:
                    new_queue.append(d)
            
            new_queue.reverse() # Oldest first
            
            for drama in new_queue:
                if not BotState.is_auto_running: break
                
                # PRIORITY CHECK
                if not BotState.manual_queue.empty():
                    logger.info("⏳ Manual request detected. Pausing Auto-Mode.")
                    while not BotState.manual_queue.empty():
                        await asyncio.sleep(5)
                    logger.info("▶️ Manual requests finished. Resuming Auto-Mode.")
                    
                book_id = str(drama.get("bookId") or drama.get("cid") or drama.get("id"))
                title = drama.get("bookName") or drama.get("title") or "Unknown"
                
                # CHECK DUPLICATE ID OR TITLE
                if book_id in processed_ids or title.strip().lower() in processed_titles:
                    continue
                
                processed_ids.add(book_id)
                # Note: We save only when success, but for now we skip them in scan if they are in sets
                # Title will be added to set upon successful upload inside process_drama_full
                
                logger.info(f"✨ New discovery: {title} ({book_id})")
                
                async with BotState.lock:
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
    
    # Start workers and auto loop
    client.loop.create_task(manual_worker())
    client.loop.create_task(auto_mode_loop())
    
    logger.info("Bot is active and monitoring.")
    client.run_until_disconnected()
