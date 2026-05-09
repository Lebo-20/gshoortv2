import asyncio
import httpx
import json

async def check():
    book_id = "31001345253" # From previous logs
    async with httpx.AsyncClient() as client:
        res = await client.get(f'https://goodshort.dramabos.my.id/book/{book_id}?lang=in')
        data = res.json()
        d = data.get("data", {})
        print("Keys in data:", list(d.keys()))
        if "book" in d:
            print("Keys in 'book':", list(d["book"].keys()))
            print("Book Name:", d["book"].get("bookName"))
            print("Title:", d["book"].get("title"))

asyncio.run(check())
