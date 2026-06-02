import asyncio
from api import get_latest_dramas, get_all_episodes
import json

async def main():
    dramas = await get_latest_dramas(pages=1)
    if not dramas:
        print("No dramas found.")
        return
    
    first_drama = dramas[0]
    book_id = first_drama.get('bookId') or first_drama.get('id')
    title = first_drama.get('title') or first_drama.get('bookName')
    
    print(f"Testing Drama: {title} (ID: {book_id})")
    
    episodes = await get_all_episodes(book_id)
    print(f"Found {len(episodes)} episodes.")
    
    if episodes:
        first_ep = episodes[0]
        print(f"First Episode Data: {json.dumps(first_ep, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
