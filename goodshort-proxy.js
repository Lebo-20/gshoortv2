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
  token:      process.env.DRAMABITE_TOKEN || 'A8D6AB170F7B89F2182561D3B32F390D', 
  lang:       'in',
  quality:    '720p',
};
// ============================================================

let videoKey  = null;    
let episodes  = {};      
let bookName  = '';
let lastFetch = {};      

const CACHE_TTL = 24 * 60 * 60 * 1000; 

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
    console.log(`[Proxy] Loaded: ${bookName} (${data.totalEpisode} eps)`);
    return true;
  } catch (e) {
    console.error('[Proxy] rawurl Error:', e.message);
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
    await fetchBook(bookId);
  }

  const m3u8Url = episodes[chapterId];
  if (!m3u8Url) return res.status(404).send('Episode not found');

  try {
    const r = await axios.get(m3u8Url, {
      headers: { 'User-Agent': 'okhttp/4.10.0' },
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
    const lines = content.split('\n').map(line => {
      const stripped = line.trim();
      if (stripped && !stripped.startsWith('#') && stripped.endsWith('.ts')) {
        const tsUrl = baseUrl + '/' + stripped;
        return `http://${host}/ts?url=${encodeURIComponent(tsUrl)}`;
      }
      return line;
    });

    res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
    res.send(lines.join('\n'));
  } catch (e) {
    res.status(502).send('Failed to fetch m3u8');
  }
});

app.get('/ts', async (req, res) => {
  const tsUrl = req.query.url;
  if (!tsUrl) return res.status(400).send('Missing url');
  try {
    const r = await axios.get(tsUrl, {
      headers: { 'User-Agent': 'okhttp/4.10.0' },
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
