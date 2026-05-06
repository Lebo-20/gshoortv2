import asyncio
from api import get_home_dramas

async def test():
    dramas = await get_home_dramas()
    if dramas:
        print(f"Ditemukan {len(dramas)} drama di home.")
        first = dramas[0]
        print(f"Judul: {first.get('title')}")
        print(f"ID: {first.get('cid') or first.get('id')}")
    else:
        print("Tidak ada drama ditemukan.")

if __name__ == "__main__":
    asyncio.run(test())
