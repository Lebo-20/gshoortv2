import os
import time
import base64
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
from typing import Dict, Any

app = FastAPI()

# ============================================================
# KONFIGURASI
# ============================================================
CONFIG = {
    "port": 3100,
    "api_base": "https://goodshort.dramabos.my.id",
    "token": "A8D6AB170F7B89F2182561D3B32F390D",
    "lang": "in",
    "quality": "720p",
}
# ============================================================

# Cache in-memory
state = {
    "video_key": None,
    "episodes": {},  # { chapterId: m3u8Url }
    "book_name": "",
    "last_fetch": {} # { bookId: timestamp }
}

CACHE_TTL = 24 * 60 * 60  # 24 jam dalam detik

async def fetch_book(book_id: str):
    now = time.time()
    if book_id in state["last_fetch"] and now - state["last_fetch"][book_id] < CACHE_TTL:
        return True

    try:
        url = f"{CONFIG['api_base']}/rawurl/{book_id}"
        params = {
            "lang": CONFIG["lang"],
            "q": CONFIG["quality"],
            "code": CONFIG["token"]
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            data = resp.json().get("data")
            
            if not data:
                return False

            state["video_key"] = data.get("videoKey")
            state["book_name"] = data.get("bookName", "")

            for ep in data.get("episodes", []):
                if ep.get("m3u8"):
                    state["episodes"][int(ep["id"])] = ep["m3u8"]

            state["last_fetch"][book_id] = now
            print(f"[rawurl] {state['book_name']} — {data.get('totalEpisode')} eps, key: {state['video_key'][:8]}...")
            return True
    except Exception as e:
        print(f"[rawurl] Error: {e}")
        return False

@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/load/{book_id}")
async def load_book(book_id: str):
    if book_id in state["last_fetch"]:
        del state["last_fetch"][book_id] # force refresh
    
    ok = await fetch_book(book_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to fetch book")
    
    return {
        "ok": True,
        "bookName": state["book_name"],
        "totalEpisode": len(state["episodes"]),
        "videoKey": state["video_key"]
    }

@app.get("/m3u8/{chapter_id}")
async def get_m3u8(chapter_id: int, request: Request, bookId: str = None):
    # Auto-fetch jika belum ada
    if chapter_id not in state["episodes"] and bookId:
        ok = await fetch_book(book_Id)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to fetch book data")

    m3u8_url = state["episodes"].get(chapter_id)
    if not m3u8_url:
        raise HTTPException(status_code=404, detail="Episode not found. Load book first: GET /load/{bookId}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(m3u8_url, headers={"User-Agent": "okhttp/4.10.0"})
            r.raise_for_status()
            
            base_url = m3u8_url[:m3u8_url.rfind('/')]
            content = r.text
            
            # Inject AES key
            if state["video_key"]:
                import re
                content = re.sub(
                    r'#EXT-X-KEY:METHOD=(AES-128|SAMPLE-AES),URI="[^"]*"',
                    r'#EXT-X-KEY:METHOD=\1,URI="/key"',
                    content
                )

            # Rewrite .ts URL
            host = request.headers.get("host")
            lines = []
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and stripped.endswith('.ts'):
                    ts_url = f"{base_url}/{stripped}"
                    lines.append(f"http://{host}/ts?url={ts_url}")
                elif stripped.startswith('#EXT-X-KEY'):
                    lines.append(stripped.replace('URI="/key"', f'URI="http://{host}/key"'))
                else:
                    lines.append(line)

            return Response(content="\n".join(lines), media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        print(f"[m3u8] Error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch m3u8 from CDN")

@app.get("/key")
async def get_key():
    if not state["video_key"]:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_bytes = base64.b64decode(state["video_key"])
    return Response(content=key_bytes, media_type="application/octet-stream")

@app.get("/ts")
async def proxy_ts(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")

    try:
        async def stream_ts():
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("GET", url, headers={"User-Agent": "okhttp/4.10.0"}) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk

        return StreamingResponse(stream_ts(), media_type="video/mp2t")
    except Exception as e:
        print(f"[ts] Error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch segment")

@app.get("/info")
async def get_info():
    return {
        "status": "ok",
        "bookName": state["book_name"],
        "cachedEpisodes": len(state["episodes"]),
        "hasVideoKey": bool(state["video_key"]),
        "quality": CONFIG["quality"],
        "lang": CONFIG["lang"],
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=CONFIG["port"])
