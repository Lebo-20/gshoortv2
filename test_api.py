import asyncio
from api import get_latest_dramas, search_dramas

async def test():
    print("Testing get_latest_dramas:")
    dramas = await get_latest_dramas(pages=1)
    print(f"Returned type: {type(dramas)}")
    print(f"Length: {len(dramas)}")
    if dramas:
        print(f"First item type: {type(dramas[0])}")
        print(f"First item: {dramas[0]}")
    
    print("\nTesting search_dramas:")
    search = await search_dramas("cinta")
    print(f"Returned type: {type(search)}")
    print(f"Length: {len(search)}")
    if search:
        print(f"First item type: {type(search[0])}")
        print(f"First item: {search[0]}")

asyncio.run(test())
