import asyncio
import httpx
import json

async def check():
    async with httpx.AsyncClient() as client:
        res = await client.get('https://goodshort.dramabos.my.id/home?page=1&lang=in')
        data = res.json()
        print("Keys in root:", data.keys())
        if "data" in data:
            d = data["data"]
            if isinstance(d, dict):
                print("Keys in data:", d.keys())
                for k, v in d.items():
                    if isinstance(v, list):
                        print(f"Key '{k}' is a list with {len(v)} items")
                        if len(v) > 0:
                            print(f"Example item in '{k}':", list(v[0].keys()))
                            if 'items' in v[0]:
                                print("Example 'items' list item:", list(v[0]['items'][0].keys()))
            elif isinstance(d, list):
                print(f"Data is a list with {len(d)} items")
                if len(d) > 0:
                    print("Example item:", list(d[0].keys()))

asyncio.run(check())
