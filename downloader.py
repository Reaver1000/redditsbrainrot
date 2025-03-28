import yt_dlp
from pathlib import Path
import subprocess

def download_youtube_video(url: str, output_dir: str = "./downloads/", filename: str = None, remove_audio: bool = True):
    """
    Downloads a YouTube video using yt-dlp and optionally removes the audio.
    """
    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Set download options
    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080][ext=mp4]",
        "outtmpl": f"{output_dir}/{filename if filename else '%(title)s'}.%(ext)s",
        "retries": 10,
        "quiet": False,
        "merge_output_format": "mp4",  # Force MP4 output
    }

    try:
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info_dict)
            print(f"✅ Downloaded: {downloaded_file}")

            # Remove audio if requested
            if remove_audio:
                output_file_no_audio = downloaded_file.replace(".mp4", "_no_audio.mp4")
                remove_audio_ffmpeg(downloaded_file, output_file_no_audio)
                print(f"✅ Audio removed: {output_file_no_audio}")
                return output_file_no_audio

            return downloaded_file
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return None

def remove_audio_ffmpeg(input_video: str, output_video: str):
    """
    Removes audio from a video using FFmpeg.
    """
    command = [
        "ffmpeg",
        "-i", input_video,
        "-c:v", "copy",  # Copy video stream without re-encoding
        "-an",           # Remove audio
        output_video
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error removing audio: {e}")

def get_user_urls():
    """
    Prompt user to enter YouTube URLs, one per line.
    """
    print("Enter YouTube URLs (one per line). Press Enter twice to finish:")
    urls = []
    while True:
        url = input().strip()
        if url == "":
            break
        urls.append(url)
    return urls

def main():
    # Predefined URLs
    predefined_urls = [
        "https://www.youtube.com/watch?v=j9vHyed-jQY",
        "https://www.youtube.com/watch?v=Lx2yQ-CVoxQ",
        "https://www.youtube.com/watch?v=ZtLrNBdXT7M",
        "https://www.youtube.com/watch?v=oAdTqkVdeeU",
        "https://www.youtube.com/watch?v=5M1zs1qJ-lw",
    ]

    # Ask user for download method
    print("Choose download method:")
    print("1. Use predefined URLs")
    print("2. Enter custom URLs")
    
    choice = input("Enter your choice (1/2): ").strip()

    # Determine which URLs to use
    if choice == '1':
        urls = predefined_urls
        print("Using predefined URLs:")
        for url in urls:
            print(url)
    elif choice == '2':
        urls = get_user_urls()
    else:
        print("Invalid choice. Using predefined URLs.")
        urls = predefined_urls

    # Ask about audio
    remove_audio = input("Remove audio from videos? (Y/n): ").strip().lower() != 'n'

    # Download each video
    for url in urls:
        print(f"🚀 Downloading video from: {url}")
        download_youtube_video(url, remove_audio=remove_audio)
        print("---")

    print("🎉 All downloads completed!")

if __name__ == "__main__":
    main()