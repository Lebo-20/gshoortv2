import api, asyncio, json, os

async def check():
    processed = set()
    if os.path.exists("processed.json"):
        with open("processed.json", "r") as f:
            processed = set(json.load(f))
            
    dramas = await api.get_latest_dramas(pages=5)
    print(f"Total dramas fetched: {len(dramas)}")
    
    new_found = []
    for d in dramas:
        bid = str(d.get("bookId") or d.get("id") or d.get("bookid", ""))
        if bid and bid not in processed:
            new_found.append(bid)
            
    print(f"New found count: {len(new_found)}")
    if new_found:
        print(f"Sample new IDs: {new_found[:10]}")
    else:
        print("No new IDs found in the first 5 pages.")
        if dramas:
            print(f"Sample fetched ID: {str(dramas[0].get('bookId') or dramas[0].get('id'))}")

asyncio.run(check())
