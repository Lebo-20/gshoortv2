import httpx
import logging

logger = logging.getLogger(__name__)

# GoodShort API Configuration
BASE_URL = "https://goodshort.dramabos.my.id"
AUTH_CODE = "A8D6AB170F7B89F2182561D3B32F390D"
LANG = "in"
PROXY_URL = "http://localhost:3100"

async def get_drama_detail(book_id: str):
    """Fetches drama detail from GoodShort API."""
    url = f"{BASE_URL}/book/{book_id}"
    params = {"lang": LANG}
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, dict):
                res_data = data.get("data")
                if res_data and isinstance(res_data, dict) and "book" in res_data:
                    return res_data.get("book")
                return res_data
            return None
        except Exception as e:
            logger.error(f"Error fetching drama detail for {book_id}: {e}")
            return None

async def get_all_episodes(book_id: str):
    """Fetches episode list from GoodShort API and normalizes for downloader."""
    url = f"{BASE_URL}/chapters/{book_id}"
    params = {
        "lang": LANG,
        "code": AUTH_CODE
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, dict):
                episodes = data.get("data", {}).get("list", [])
                normalized = []
                for ep in episodes:
                    if not isinstance(ep, dict):
                        continue
                        
                    chapter_id = ep.get("id")
                    if not chapter_id: continue
                    
                    # Construct URL using the proxy server
                    proxy_m3u8 = f"{PROXY_URL}/m3u8/{chapter_id}?bookId={book_id}"
                    
                    normalized.append({
                        "episode": ep.get("index", -1) + 1 if "index" in ep else (ep.get("chapterName") or ep.get("id")),
                        "id": chapter_id,
                        "title": ep.get("chapterName") or f"Episode {ep.get('index', 0)+1}",
                        "videos": [
                            {
                                "url": proxy_m3u8,
                                "quality": "720P"
                            }
                        ]
                    })
                return normalized
            return []
        except Exception as e:
            logger.error(f"Error fetching episodes for {book_id}: {e}")
            return []

async def get_latest_dramas(pages=1, types=None, channel=-1):
    """Fetches latest dramas from GoodShort home/hot sections."""
    all_dramas = []
    
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, pages + 1):
            if types and "populersearch" in types:
                url = f"{BASE_URL}/populersearch"
                params = {"lang": LANG}
            elif types and "hot" in types:
                url = f"{BASE_URL}/hot"
                params = {"lang": LANG}
            else:
                url = f"{BASE_URL}/home"
                params = {"lang": LANG, "channel": channel, "page": page, "size": 20}
                
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    raw_data = data.get("data", [])
                    
                    items = []
                    if isinstance(raw_data, list):
                        items = raw_data
                    elif isinstance(raw_data, dict):
                        records = raw_data.get("records", [])
                        for rec in records:
                            rec_items = rec.get("items", [])
                            if isinstance(rec_items, list):
                                items.extend(rec_items)
                        
                        sections = raw_data.get("sections", [])
                        for s in sections:
                            sec_data = s.get("data", [])
                            if isinstance(sec_data, list):
                                items.extend(sec_data)
                    
                    if not items:
                        break
                    all_dramas.extend(items)
                    
                    if types and ("populersearch" in types or "hot" in types):
                        break
                else:
                    break
            except Exception as e:
                logger.error(f"Error fetching latest dramas page {page}: {e}")
                break
                
    return all_dramas

async def search_dramas(keyword: str, pages=1):
    """Searches dramas by keyword using GoodShort API."""
    all_dramas = []
    
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}/search"
            params = {
                "lang": LANG,
                "q": keyword,
                "page": page,
                "size": 15
            }
                
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("data", [])
                    if not items:
                        break
                    all_dramas.extend(items)
                else:
                    break
            except Exception as e:
                logger.error(f"Error searching page {page}: {e}")
                break
    
    return all_dramas
