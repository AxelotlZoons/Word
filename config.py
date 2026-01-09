import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Live NPR MP3 Stream (Low Latency)
    # STREAM_URL = "https://npr-ice.streamguys1.com/live.mp3"
    STREAM_URL = "https://www.youtube.com/watch?v=iEpJwprxDdk"
    MARKET_TICKER = "KXHOCHULMENTION-26JAN14-TRUM"

    # Define what you are looking for
    KEYWORDS = {"npr", "trump", "agent", "ice", "senate", "democrat", "republican"}
    # KEYWORDS = {"npr", "trump", "fire", "house", "senate", "insurance"}
    # KEYWORDS = {"npr", "career", "film", "career", "you", "news"}
    # KEYWORDS = {"yes", "npr", "moment", "film", "career", "her", "news"}

    DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
    if not DEEPGRAM_API_KEY:
        raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
    
    # Deepgram WebSocket Configuration
    DEEPGRAM_URL = (
        "wss://api.deepgram.com/v1/listen"
        "?model=nova-2"
        "&language=en"
        "&interim_results=false"
        "&smart_format=false"
        "&punctuate=false"
        "&encoding=linear16"
        "&sample_rate=16000"
    )

    KALSHI_API_KEY_ID = os.environ.get("KALSHI_API_KEY_ID")
    KALSHI_PRIVATE_KEY_PATH = "kalshi_private_key.pem"