import httpx

async def main():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:3100/m3u8/18094613?bookId=31001370470")
        print(resp.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
