import asyncio
from api import get_home_dramas

async def main():
    items = await get_home_dramas()
    for i in items[:15]:
        print(f"{i.get('bookId')}: {i.get('bookName')}")

if __name__ == "__main__":
    asyncio.run(main())
