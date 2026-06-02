import asyncio
import httpx
import os

async def test_dramabite_rawurl(book_id):
    BASE_URL = "https://dramabite.dramabos.online"
    AUTH_CODE = "A8D6AB170F7B89F2182561D3B32F390D"
    
    # Try to fetch rawurl for episode 1 (or the book itself if rawurl supports it)
    # Usually it's rawurl/chapterId
    url = f"{BASE_URL}/rawurl/{book_id}?lang=id&q=720p&code={AUTH_CODE}"
    
    print(f"Testing DramaBite RawURL: {url}")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_dramabite_rawurl("10873"))
