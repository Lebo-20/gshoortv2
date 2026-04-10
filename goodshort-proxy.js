/**
 * GoodShort Video Proxy Server
 * Node.js — siap pakai di VPS sendiri
 *
 * Install:
 *   npm install express axios
 *
 * Jalankan:
 *   node goodshort-proxy.js
 *
 * Endpoint yang tersedia:
 *   GET /m3u8/:chapterId   — proxy + modifikasi m3u8 (inject key, rewrite .ts)
 *   GET /ts?url=...        — proxy .ts segment dengan CORS header
 */

const express = require('express');
const axios   = require('axios');
const app     = express();

// ============================================================
// KONFIGURASI — edit bagian ini
// ============================================================
const CONFIG = {
  port:       3100,
  apiBase:    'https://goodshort.dramabos.my.id',
  token:      'A8D6AB170F7B89F2182561D3B32F390D',    // dari bot @nanomilkisbot
  lang:       'in',
  quality:    '720p',
};
// ============================================================

// Cache in-memory
let videoKey  = null;    // AES-128 key (base64)
let episodes  = {};      // { chapterId: m3u8Url }
let bookName  = '';
let lastFetch = {};      // { bookId: timestamp }

const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 jam

// Ambil data dari /rawurl/ dan simpan ke cache
async function fetchBook(bookId) {
  const now = Date.now();
  if (lastFetch[bookId] && now - lastFetch[bookId] < CACHE_TTL) return true;

  try {
    const url = `${CONFIG.apiBase}/rawurl/${bookId}?lang=${CONFIG.lang}&q=${CONFIG.quality}&code=${CONFIG.token}`;
    const res = await axios.get(url, { timeout: 15000 });
    const data = res.data?.data;
    if (!data) return false;

    videoKey = data.videoKey;
    bookName = data.bookName || '';

    for (const ep of (data.episodes || [])) {
      if (ep.m3u8) episodes[ep.id] = ep.m3u8;
    }

    lastFetch[bookId] = now;
    console.log(`[rawurl] ${bookName} — ${data.totalEpisode} eps, key: ${videoKey?.slice(0,8)}...`);
    return true;
  } catch (e) {
    console.error('[rawurl] Error:', e.message);
    return false;
  }
}

// CORS middleware
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// ============================================================
// GET /load/:bookId — preload data buku ke cache
// ============================================================
app.get('/load/:bookId', async (req, res) => {
  const { bookId } = req.params;
  delete lastFetch[bookId]; // force refresh
  const ok = await fetchBook(bookId);
  if (!ok) return res.status(500).json({ error: 'Failed to fetch book' });
  const epIds = Object.keys(episodes);
  res.json({ ok: true, bookName, totalEpisode: epIds.length, videoKey });
});

// ============================================================
// GET /m3u8/:chapterId?bookId=xxx — proxy + modifikasi m3u8
// ============================================================
app.get('/m3u8/:chapterId', async (req, res) => {
  const chapterId = parseInt(req.params.chapterId);
  const bookId    = req.query.bookId;

  // Auto-fetch jika belum ada
  if (!episodes[chapterId] && bookId) {
    const ok = await fetchBook(bookId);
    if (!ok) return res.status(500).send('Failed to fetch book data');
  }

  const m3u8Url = episodes[chapterId];
  if (!m3u8Url) return res.status(404).send('Episode not found. Load book first: GET /load/:bookId');

  try {
    const r = await axios.get(m3u8Url, {
      headers: { 'User-Agent': 'okhttp/4.10.0' },
      timeout: 10000,
      responseType: 'text',
    });

    const baseUrl = m3u8Url.substring(0, m3u8Url.lastIndexOf('/'));
    let content   = r.data;

    // Inject AES key sebagai raw binary URL proxy
    if (videoKey) {
      content = content.replace(
        /#EXT-X-KEY:METHOD=(AES-128|SAMPLE-AES),URI="[^"]*"/g,
        `#EXT-X-KEY:METHOD=$1,URI="/key"`
      );
    }

    // Rewrite .ts URL → proxy /ts?url=...
    const proto = req.headers['x-forwarded-proto'] || 'http';
    const host  = req.headers['x-forwarded-host'] || req.headers.host;
    const lines = content.split('\n').map(line => {
      const stripped = line.trim();
      if (stripped && !stripped.startsWith('#') && stripped.endsWith('.ts')) {
        const tsUrl = baseUrl + '/' + stripped;
        // Prefix with full host url so ffmpeg resolves it easily
        return `http://${host}/ts?url=${encodeURIComponent(tsUrl)}`;
      }
      if (stripped.startsWith('#EXT-X-KEY')) {
         // Also prepend localhost to the key
         return stripped.replace('URI="/key"', `URI="http://${host}/key"`);
      }
      return line;
    });

    res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
    res.send(lines.join('\n'));
  } catch (e) {
    console.error('[m3u8] Error:', e.message);
    res.status(502).send('Failed to fetch m3u8 from CDN');
  }
});

// ============================================================
// GET /key — proxy raw AES key
// ============================================================
app.get('/key', (req, res) => {
  if (!videoKey) return res.status(404).send('Key not found');
  const buffer = Buffer.from(videoKey, 'base64');
  res.setHeader('Content-Type', 'application/octet-stream');
  res.send(buffer);
});

// ============================================================
// GET /ts?url=... — proxy .ts segment
// ============================================================
app.get('/ts', async (req, res) => {
  const tsUrl = req.query.url;
  if (!tsUrl) return res.status(400).send('Missing url parameter');

  try {
    const r = await axios.get(tsUrl, {
      headers: { 'User-Agent': 'okhttp/4.10.0' },
      responseType: 'stream',
      timeout: 15000,
    });

    res.setHeader('Content-Type', 'video/mp2t');
    r.data.pipe(res);
  } catch (e) {
    console.error('[ts] Error:', e.message);
    res.status(502).send('Failed to fetch segment');
  }
});

// ============================================================
// GET /info — status server
// ============================================================
app.get('/info', (req, res) => {
  res.json({
    status: 'ok',
    bookName,
    cachedEpisodes: Object.keys(episodes).length,
    hasVideoKey: !!videoKey,
    quality: CONFIG.quality,
    lang: CONFIG.lang,
  });
});

// ============================================================
app.listen(CONFIG.port, () => {
  console.log(`GoodShort Proxy running on port ${CONFIG.port}`);
  console.log(`Load buku: GET http://localhost:${CONFIG.port}/load/{bookId}`);
  console.log(`Play ep  : GET http://localhost:${CONFIG.port}/m3u8/{chapterId}?bookId={bookId}`);
  console.log(`Info     : GET http://localhost:${CONFIG.port}/info`);
});
