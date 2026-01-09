import aiohttp
import time
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class Kalshi:
    def __init__(self, api_key_id, private_key_path):
        self.host = "https://api.elections.kalshi.com/trade-api/v2"
        self.api_key_id = api_key_id
        self.session = None
        
        # Load the RSA Private Key from the file
        try:
            with open(private_key_path, "rb") as key_file:
                self.private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find key file at: {private_key_path}")

    async def connect(self):
        """Opens the HTTP session."""
        self.session = aiohttp.ClientSession()
        print(f"[Kalshi] API connected. Auth ID: {self.api_key_id[:5]}...")

    async def close(self):
        """Closes the HTTP session."""
        if self.session:
            await self.session.close()

    def _get_headers(self):
        """Generates the signed headers required by Kalshi."""
        # 1. Get current timestamp (milliseconds)
        timestamp = str(int(time.time() * 1000))
        
        # 2. Sign the timestamp with your Private Key
        msg = timestamp.encode('utf-8')
        signature = self.private_key.sign(
            msg,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # 3. Return the headers
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode('utf-8'),
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

    async def get_market_price(self, ticker):
        """
        Fetches the current COST to BUY 'Yes'.
        Logic: 100 cents - Best 'No' Bid
        """
        if not self.session:
            await self.connect()

        url = f"{self.host}/markets/{ticker}/orderbook"
        headers = self._get_headers()

        try:
            start_time = time.time()
            async with self.session.get(url, headers=headers) as resp:
                data = await resp.json()
                latency = (time.time() - start_time) * 1000
                
                orderbook = data.get("orderbook", {})
                
                # KALSHI TRICK: The 'Ask' for Yes is actually (100 - Best Bid for No)
                # We need to find the HIGHEST price someone is willing to pay for 'No'.
                no_bids = orderbook.get("no", [])
                
                if no_bids:
                    # no_bids is sorted Low -> High. The last one is the BEST bid.
                    best_no_bid = no_bids[-1][0] 
                    
                    # The price to BUY Yes is 100 minus that No bid
                    buy_price = 100 - best_no_bid
                    
                    return buy_price, latency
                else:
                    # If nobody is bidding on 'No', then nobody is selling 'Yes'.
                    print(f"[Kalshi] No sellers found for {ticker}")
                    return None, latency

        except Exception as e:
            print(f"[Kalshi] Error: {e}")
            return None, 0