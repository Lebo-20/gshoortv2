import httpx
import logging
import os

logger = logging.getLogger(__name__)

BASE_URL = "https://goodshort.dramabos.my.id"
AUTH_CODE = os.getenv("DRAMABITE_TOKEN", "A8D6AB170F7B89F2182561D3B32F390D")

async def get_drama_detail(book_id: str):
    url = f"{BASE_URL}/book/{book_id}"
    params = {"lang": "in"}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            # GoodShort usually returns { "data": { ... } }
            return data.get("data") if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"Error fetching drama detail for {book_id}: {e}")
            return None

async def get_all_episodes(book_id: str):
    url = f"{BASE_URL}/chapters/{book_id}"
    params = {"lang": "in", "code": AUTH_CODE}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            res_data = data.get("data", []) if isinstance(data, dict) else []
            if isinstance(res_data, dict) and "list" in res_data:
                return res_data["list"]
            return res_data
        except Exception as e:
            logger.error(f"Error fetching episodes for {book_id}: {e}")
            return []

async def get_latest_dramas(pages=1, types=None):
    """Fetches latest dramas from GoodShort home."""
    all_dramas = []
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}/home"
            params = {"page": page, "lang": "in", "size": 20, "channel": -1}
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    # GoodShort structure: data.data.records -> each record has an 'items' list
                    records = data.get("data", {}).get("records", []) if isinstance(data.get("data"), dict) else []
                    page_dramas = []
                    for record in records:
                        if isinstance(record, dict) and "items" in record:
                            page_dramas.extend(record["items"])
                    
                    logger.info(f"Page {page}: Found {len(page_dramas)} items in {len(records)} records")
                    all_dramas.extend(page_dramas)
                else:
                    break
            except Exception as e:
                logger.error(f"Error fetching home page {page}: {e}")
                break
    return all_dramas

async def get_home_dramas():
    return await get_latest_dramas(pages=1)

async def search_dramas(query: str):
    url = f"{BASE_URL}/search"
    params = {"q": query, "lang": "in", "page": 1, "size": 15, "code": AUTH_CODE}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            search_result = data.get("data", {}).get("searchResult", {}) if isinstance(data.get("data"), dict) else {}
            records = search_result.get("records", []) if isinstance(search_result, dict) else []
            return records if isinstance(records, list) else []
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            return []

async def get_token():
    return AUTH_CODE

# Backwards compatibility names
get_latest_idramas = get_home_dramas
get_idrama_detail = get_drama_detail
get_idrama_all_episodes = get_all_episodes
