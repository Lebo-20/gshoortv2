import asyncio
import httpx
import json

async def check():
    async with httpx.AsyncClient() as client:
        res = await client.get('https://goodshort.dramabos.my.id/home?page=1&lang=in')
        data = res.json()
        records = data.get("data", {}).get("records", [])
        print(f"Found {len(records)} records")
        for i, rec in enumerate(records):
            items = rec.get("items", [])
            print(f"Record {i} ({rec.get('style', 'no style')}): {len(items)} items")
            if len(items) > 0:
                # Check keys of the first item
                print(f"  First item keys: {list(items[0].keys())}")
                print(f"  First item Book ID: {items[0].get('bookId')} | ID: {items[0].get('id')}")

asyncio.run(check())
