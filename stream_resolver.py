import yt_dlp

def get_audio_stream_url(target_url):
    """
    Resolves the direct audio stream URL for YouTube, Twitch, and others.
    If the URL is already a direct stream (MP3/M3U8), it returns it as-is.
    """
    
    # Simple check: If it looks like a YouTube or Twitch link, we need to extract it.
    complex_services = ["youtube", "twitch"]
    
    if any(service in target_url for service in complex_services):
        print(f"[Resolver] Detected complex URL.")
        print(f"[Resolver] Extracting audio feed...")
        
        # Configure yt-dlp to find the best audio stream without downloading it
        ydl_opts = {
            'format': 'bestaudio/best',  # Look for audio-only first
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            
            # For live streams, the 'url' key is usually the m3u8 master playlist
            raw_url = info.get('url')
            print(f"[Resolver] Success. Stream URL found.")
            return raw_url
                
            
    # If it's not YouTube/Twitch, assume it's a direct MP3/Icecast link
    return target_url