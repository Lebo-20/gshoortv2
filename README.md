# 🎬 GoodShort Automation Bot

Sistem otomatisasi untuk mendownload, menggabungkan episode, dan mengupload drama GoodShort ke Telegram.

## 📋 Prasyarat
1. **Node.js** (v16 atau lebih baru)
2. **Python** (v3.10 atau lebih baru)
3. **FFmpeg** (Wajib terinstal di sistem)

---

## 🚀 Cara Instalasi

### 1. Kloning Repositori
```bash
git clone https://github.com/Lebo-20/gshoortv2.git
cd gshoortv2
```

### 2. Instal Dependensi Node.js (untuk Proxy)
```bash
npm install express axios
```

### 3. Instal Dependensi Python (untuk Bot)
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi
Edit file `.env` dan masukkan API_ID, API_HASH, serta BOT_TOKEN Anda.

---

## 🏃‍♂️ Cara Menjalankan

### Metode A: Manual (Dua Terminal)
Buka dua terminal berbeda:

**Terminal 1 (Proxy):**
```bash
node goodshort-proxy.js
```

**Terminal 2 (Bot):**
```bash
python main.py
```

---

### Metode B: Menggunakan PM2 (Rekomendasi VPS)
Agar script jalan terus di background dan auto-restart jika error.

1. **Instal PM2:** `npm install -g pm2`
2. **Jalankan Proxy:** `pm2 start goodshort-proxy.js --name "proxy-video"`
3. **Jalankan Bot:** `pm2 start main.py --name "bot-drama" --interpreter python3`
4. **Cek Status:** `pm2 status`
5. **Cek Log:** `pm2 logs`

---

## 🎮 Perintah Bot Admin
- `/panel` - Membuka kontrol panel (Otomatis menghentikan auto-mode).
- `/cari {judul}` - Mencari drama berdasarkan judul.
- `/download {bookId}` - Mendownload drama secara manual.
- `/update` - Menarik pembaruan terbaru dari GitHub.

---

## 💡 Fitur Terbaru
- **Auto-Continue**: Jika ada video yang gagal, bot akan lanjut ke video berikutnya tanpa berhenti.
- **Auto-Stop on Panel**: Bot akan otomatis berhenti (pause) saat admin menggunakan `/panel`.
- **Bypass 10 Menit**: Menggunakan proxy khusus untuk mendekripsi video yang diproteksi.
