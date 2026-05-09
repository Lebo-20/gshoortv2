import asyncio
from api import get_latest_dramas

async def test():
    res = await get_latest_dramas(pages=1)
    print("Len:", len(res))
    if len(res) > 0:
        print("Type first:", type(res[0]))
        if isinstance(res[0], str):
            print("First item:", res[0])

asyncio.run(test())
