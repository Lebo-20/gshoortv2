import asyncio
import httpx
import json

async def check():
    book_id = "31001345253" # From previous logs
    async with httpx.AsyncClient() as client:
        res = await client.get(f'https://goodshort.dramabos.my.id/book/{book_id}?lang=in')
        data = res.json()
        d = data.get("data", {})
        # Print only metadata, not chapters
        metadata = {k: v for k, v in d.items() if k != "chapters"}
        print(json.dumps(metadata, indent=2))

asyncio.run(check())
