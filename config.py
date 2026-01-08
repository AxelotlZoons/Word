import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Live NPR MP3 Stream (Low Latency)
    STREAM_URL = "https://npr-ice.streamguys1.com/live.mp3"

    # Define what you are looking for
    KEYWORDS = {"venezuela", "fire", "emergency", "president", "china"}

    DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
    if not DEEPGRAM_API_KEY:
        raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
    
    # Deepgram WebSocket Configuration
    DEEPGRAM_URL = (
        "wss://api.deepgram.com/v1/listen"
        "?model=nova-2"
        "&language=en"
        "&interim_results=true"
        "&smart_format=false"
        "&punctuate=false"
        "&encoding=linear16"
        "&sample_rate=16000"
    )