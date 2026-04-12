# 🎬 GoodShort Automation Bot (Pure Python)

Sistem otomatisasi profesional untuk mendownload, menggabungkan episode (Merge), dan mengupload drama dari platform GoodShort ke Telegram secara otomatis. Sekarang sepenuhnya berjalan di **Python 3**.

## 🌟 Fitur Unggulan
- **100% Python Logic**: Tidak perlu menginstal Node.js lagi.
- **Full Auto-Mode**: Bot otomatis mencari dan mengupload drama terbaru secara berkala.
- **Telegram Topic Support**: Mendukung pengiriman ke grup dengan topik (Forum mode).
- **Auto Merge**: Secara otomatis menggabungkan puluhan episode menjadi satu file video utuh.
- **Python Proxy**: Bypass proteksi durasi video (mencegah video terpotong 10 menit).
- **Control Panel**: Admin dapat mengontrol bot langsung melalui Telegram.

---

## 📋 Prasyarat
- **Python** (v3.10+)
- **FFmpeg** (Wajib terinstal di sistem/VPS)

---

## 🚀 Cara Instalasi (Putty/SSH)

### 1. Kloning Repositori
```bash
git clone https://github.com/Lebo-20/gshoortv2.git
cd gshoortv2
```

### 2. Instal Dependensi
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment
Buat file bernama `.env` di folder utama:
```bash
nano .env
```
Masukkan data berikut:
```env
API_ID=30653860
API_HASH=98e0a87077d4fc642ce183dfd7f46a19
BOT_TOKEN=8635870532:AAG1FbeoybPAUeNwU3NCmf1NBiJMJWPfYmU
ADMIN_ID=5888747846
AUTO_CHANNEL=-1003857149032
MESSAGE_THREAD_ID=1795
DATABASE_URL="postgresql://user:pass@host/db"
```

---

## 🏃‍♂️ Cara Menjalankan (Rekomendasi VPS)

Gunakan **PM2** agar bot tetap berjalan di background dan otomatis restart jika terjadi error/crash.

### 1. Jalankan Proxy & Bot
```bash
# Jalankan Proxy Video (Python)
pm2 start "python3 proxy.py" --name "gs-proxy"

# Jalankan Bot Logika (Python)
pm2 start "python3 main.py" --name "gs-bot"
```

### 2. Perintah Penting PM2
Berikut adalah daftar perintah untuk memantau bot Anda:
- **Melihat Log:** `pm2 logs`
- **Melihat Status:** `pm2 status`
- **Restart Bot:** `pm2 restart gs-bot`
- **Restart Proxy:** `pm2 restart gs-proxy`
- **Stop Semua:** `pm2 stop all`

---

## 🎮 Perintah Bot (Khusus Admin)
- `/panel` - Membuka kontrol panel (Otomatis menghentikan auto-mode).
- `/cari {judul}` - Mencari drama berdasarkan kata kunci.
- `/download {bookId}` - Download manual menggunakan ID drama.
- `/update` - Update kode bot langsung dari GitHub (Auto-restart).

---

## ⚠️ Catatan Penting
- Pastikan `ffmpeg` terinstal: `sudo apt update && sudo apt install ffmpeg -y`
- Bot menggunakan port `3100` untuk proxy lokal.
