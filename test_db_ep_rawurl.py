import asyncio
import httpx

async def get_eps(book_id):
    BASE_URL = "https://dramabite.dramabos.online"
    AUTH_CODE = "A8D6AB170F7B89F2182561D3B32F390D"
    url = f"{BASE_URL}/episodes/{book_id}?lang=id&code={AUTH_CODE}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        eps = resp.json()
        if eps:
            print(f"First Ep: {eps[0]}")
            return eps[0].get('vid') or eps[0].get('episode') or eps[0].get('id')
    return None

async def main():
    vid = await get_eps("10873")
    if vid:
        BASE_URL = "https://dramabite.dramabos.online"
        AUTH_CODE = "A8D6AB170F7B89F2182561D3B32F390D"
        url = f"{BASE_URL}/rawurl/{vid}?lang=id&q=720p&code={AUTH_CODE}"
        print(f"Testing Ep RawURL: {url}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")

if __name__ == "__main__":
    asyncio.run(main())
