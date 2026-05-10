const express = require('express');
const axios   = require('axios');
const dotenv  = require('dotenv');
const app     = express();

dotenv.config();

// ============================================================
// KONFIGURASI
// ============================================================
const CONFIG = {
  port:       3100,
  apiBase:    'https://goodshort.dramabos.my.id',
  token:      process.env.GOODSHORT_TOKEN || 'A8D6AB170F7B89F2182561D3B32F390D', 
  lang:       'in',
  quality:    '720p',
};
// ============================================================

let videoKey  = null;    
let episodes  = {};      
let bookName  = '';
let lastFetch = {};      

const CACHE_TTL = 24 * 60 * 60 * 1000; 

async function fetchBook(bookId, chapterId = null) {
  const now = Date.now();
  // Jika mencari bookId dan sudah ada di cache, skip
  if (!chapterId && lastFetch[bookId] && now - lastFetch[bookId] < CACHE_TTL) return true;
  // Jika mencari chapterId dan sudah ada di cache, skip
  if (chapterId && episodes[chapterId]) return true;

  try {
    const idToFetch = chapterId || bookId;
    console.log(`[Proxy] Fetching rawurl for ID: ${idToFetch}...`);
    const url = `${CONFIG.apiBase}/rawurl/${idToFetch}?lang=${CONFIG.lang}&q=${CONFIG.quality}&code=${CONFIG.token}`;
    const res = await axios.get(url, { timeout: 30000 });
    const data = res.data?.data;
    if (!data) return false;

    // Update global key jika ada yang baru
    if (data.videoKey) videoKey = data.videoKey;
    if (data.bookName) bookName = data.bookName;

    // Masukkan semua episode yang didapat ke dalam cache
    const fetchedEps = data.episodes || [];
    if (fetchedEps.length > 0) {
      for (const ep of fetchedEps) {
        if (ep.m3u8) episodes[ep.id] = ep.m3u8;
      }
    } else if (data.m3u8 && chapterId) {
      // Jika yang dipanggil adalah ID episode langsung, biasanya m3u8 ada di root data
      episodes[chapterId] = data.m3u8;
    }

    if (!chapterId) lastFetch[bookId] = now;
    console.log(`[Proxy] Success! Cached ${Object.keys(episodes).length} total episodes.`);
    return true;
  } catch (e) {
    console.error(`[Proxy] rawurl Error for ${chapterId || bookId}:`, e.message);
    return false;
  }
}

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.get('/load/:bookId', async (req, res) => {
  const { bookId } = req.params;
  const ok = await fetchBook(bookId);
  if (!ok) return res.status(500).json({ error: 'Failed to fetch book' });
  res.json({ ok: true, bookName, totalEpisode: Object.keys(episodes).length });
});

app.get('/m3u8/:chapterId', async (req, res) => {
  const chapterId = parseInt(req.params.chapterId);
  const bookId    = req.query.bookId;

  if (!episodes[chapterId] && bookId) {
    await fetchBook(bookId, chapterId);
  }

  const m3u8Url = episodes[chapterId];
  if (!m3u8Url) return res.status(404).send('Episode not found');

  try {
    const r = await axios.get(m3u8Url, {
      headers: { 'User-Agent': 'okhttp/3.12.13' },
      timeout: 10000,
      responseType: 'text',
    });

    const baseUrl = m3u8Url.substring(0, m3u8Url.lastIndexOf('/'));
    let content   = r.data;

    if (videoKey) {
      content = content.replace(
        /URI="local:\/\/[^"]*"/g,
        `URI="data:text/plain;base64,${videoKey}"`
      );
    }

    const host  = req.headers.host;
    let segmentCount = 0;
    const lines = content.split('\n').map(line => {
      const stripped = line.trim();
      if (stripped && !stripped.startsWith('#')) {
        segmentCount++;
        let tsUrl = stripped;
        if (!stripped.startsWith('http')) {
          tsUrl = baseUrl + '/' + stripped;
        }
        return `http://${host}/ts?url=${encodeURIComponent(tsUrl)}`;
      }
      return line;
    });

    console.log(`[Proxy] Served m3u8 for ${chapterId} (${segmentCount} segments)`);
    res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
    res.send(lines.join('\n'));
  } catch (e) {
    console.error('[Proxy] m3u8 Error:', e.message);
    res.status(502).send('Failed to fetch m3u8');
  }
});

app.get('/ts', async (req, res) => {
  const tsUrl = req.query.url;
  if (!tsUrl) return res.status(400).send('Missing url');
  try {
    const r = await axios.get(tsUrl, {
      headers: { 'User-Agent': 'okhttp/3.12.13' },
      responseType: 'stream',
      timeout: 20000,
    });
    res.setHeader('Content-Type', 'video/mp2t');
    r.data.pipe(res);
  } catch (e) {
    res.status(502).send('TS Error');
  }
});

app.get('/status', (req, res) => {
  res.json({ status: 'online', uptime: process.uptime() });
});

app.listen(CONFIG.port, () => {
  console.log(`GoodShort Proxy running on port ${CONFIG.port}`);
});
