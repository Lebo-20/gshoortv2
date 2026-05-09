import asyncio
import httpx

BASE_URL = "https://dramabite.dramabos.my.id"
AUTH_CODE = "A8D6AB170F7B89F2182561D3B32F390D"

async def inspect_dramabite(book_id):
    print(f"Inspecting DramaBite Book: {book_id}")
    
    # 1. Get episodes
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{BASE_URL}/episodes/{book_id}"
        params = {"lang": "id", "code": AUTH_CODE}
        resp = await client.get(url, params=params)
        data = resp.json()
        print(f"Response Data: {data}")
        
        episodes = data.get('data', []) if isinstance(data, dict) else data
        print(f"Total Episodes: {len(episodes)}")
        
        if episodes and isinstance(episodes, list):
            ep = episodes[0]
            m3u8_url = ep.get('url') or ep.get('playUrl')
            print(f"First Episode M3U8 URL: {m3u8_url}")
            
            # 2. Get M3U8 content
            r_m3u8 = await client.get(m3u8_url, headers={"User-Agent": "Mozilla/5.0"})
            print("--- M3U8 CONTENT ---")
            print(r_m3u8.text[:1000]) # First 1000 chars
            print("--- END ---")

if __name__ == "__main__":
    # Sample ID for DramaBite
    asyncio.run(inspect_dramabite("10960"))
