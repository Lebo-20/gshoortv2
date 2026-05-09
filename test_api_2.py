import asyncio
from api import get_latest_dramas

async def test():
    res = await get_latest_dramas(pages=1)
    print("Items:", [type(x) for x in res[:10]])
    print("First item:", res[0] if res else None)

asyncio.run(test())
