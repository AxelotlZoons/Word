import asyncio
from config import Config
from kalshi import Kalshi

async def test():
    print("--- Testing Kalshi Connection ---")
    
    # Initialize
    api = Kalshi(Config.KALSHI_API_KEY_ID, Config.KALSHI_PRIVATE_KEY_PATH)
    
    try:
        # Connect
        await api.connect()
        
        # Check Price
        print(f"Checking Price for: {Config.MARKET_TICKER}")
        price, latency = await api.get_market_price(Config.MARKET_TICKER)
        
        if price:
            print(f"✅ SUCCESS!")
            print(f"Current Price for 'Yes': {price} cents")
            print(f"API Latency: {latency:.0f}ms")
        else:
            print("❌ Connected, but no price found (Market might be closed/empty).")
            
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(test())