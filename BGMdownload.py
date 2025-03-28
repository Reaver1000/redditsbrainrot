import os
from pytube import YouTube

def download_bgm(bgm_folder='BackgroundMusic'):
    """
    Simple BGM downloader
    """
    # Ensure folders exist
    os.makedirs(bgm_folder, exist_ok=True)

    print("🎵 Background Music Downloader 🎵")
    print("Paste a YouTube URL to download background music")
    print("Press Enter without a URL to exit")

    while True:
        url = input("YouTube URL: ").strip()
        
        if not url:
            break
        
        try:
            # Validate YouTube URL
            yt = YouTube(url)
            
            # Generate filename with 'yt_' prefix
            filename = f"yt_{yt.title[:50].replace(' ', '_')}.mp3"
            output_path = os.path.join(bgm_folder, filename)

            # Download audio
            audio_streams = yt.streams.filter(only_audio=True)
            best_audio = audio_streams.first()
            best_audio.download(output_path=bgm_folder, filename=filename)

            print(f"✅ Downloaded BGM: {yt.title}")

        except Exception as e:
            print(f"❌ Error downloading BGM: {e}")

if __name__ == "__main__":
    download_bgm()