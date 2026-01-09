import asyncio
import aiohttp
from config import Config
from kalshi import Kalshi

async def find_tickers():
    print("--- Searching for Valid Tickers ---")
    
    # 1. Initialize API
    api = Kalshi(Config.KALSHI_API_KEY_ID, Config.KALSHI_PRIVATE_KEY_PATH)
    await api.connect()

    try:
        # 2. Search for the series (The part after /markets/ in the URL)
        # Based on your previous URL, the series is likely "KXHOCHULMENTION"
        # If this returns nothing, try "KXHOCHUL"
        series_ticker = "KXHOCHULMENTION" 
        
        url = f"{api.host}/markets?series_ticker={series_ticker}"
        headers = api._get_headers()

        async with api.session.get(url, headers=headers) as resp:
            data = await resp.json()
            
            markets = data.get("markets", [])
            if not markets:
                print(f"❌ No markets found for series '{series_ticker}'")
                print("Try checking the URL of the page again.")
                return

            print(f"✅ Found {len(markets)} active markets:\n")
            for m in markets:
                # Print the Ticker and the Subtitle (e.g., "Trump")
                print(f"🎯 SUBTITLE: {m.get('subtitle')} ({m.get('yes_sub_title', '')})")
                print(f"   TICKER:   {m.get('ticker')}")
                print(f"   STATUS:   {m.get('status')}")
                print("-" * 30)

    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(find_tickers())