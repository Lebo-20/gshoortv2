import asyncio
from api import get_latest_dramas

async def test():
    res = await get_latest_dramas(pages=2)
    print("Len:", len(res))
    if len(res) > 0:
        print("Type first:", type(res[0]))

asyncio.run(test())
