import asyncio
from api import get_drama_detail, get_all_episodes
import json
import sys

async def main():
    book_id = sys.argv[1] if len(sys.argv) > 1 else "31001370470"
    print(f"Testing Drama ID: {book_id}")
    
    detail = await get_drama_detail(book_id)
    if detail:
        title = detail.get('title') or detail.get('bookName')
        print(f"Title: {title}")
    
    episodes = await get_all_episodes(book_id)
    print(f"Found {len(episodes)} episodes.")
    
    if episodes:
        first_ep = episodes[0]
        print(f"First Episode ID: {first_ep.get('id')}")

if __name__ == "__main__":
    asyncio.run(main())
