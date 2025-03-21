import yt_dlp
from pathlib import Path
import subprocess

def download_youtube_video(url: str, output_dir: str = "./downloads/", filename: str = None, remove_audio: bool = True):
    """
    Downloads a YouTube video using yt-dlp and optionally removes the audio.

    Args:
        url (str): The YouTube video URL.
        output_dir (str): The directory to save the video.
        filename (str): The name of the output file (without extension). If None, the video title is used.
        remove_audio (bool): Whether to remove the audio from the downloaded video.
    """
    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Set download options
    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080][ext=mp4]",  # Best quality up to 1080p
        "outtmpl": f"{output_dir}/{filename if filename else '%(title)s'}.%(ext)s",  # Output file name
        "retries": 10,  # Retry up to 10 times
        "quiet": False,  # Show yt-dlp output
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

    Args:
        input_video (str): Path to the input video file.
        output_video (str): Path to save the output video (without audio).
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

def main():
    # Paste your YouTube video URLs here
    video_urls = [
        "https://www.youtube.com/watch?v=j9vHyed-jQY",
        "https://www.youtube.com/watch?v=Lx2yQ-CVoxQ",
        "https://www.youtube.com/watch?v=ZtLrNBdXT7M",
	"https://www.youtube.com/watch?v=oAdTqkVdeeU",
	"https://www.youtube.com/watch?v=5M1zs1qJ-lw",

    ]

    # Download each video and remove audio
    for url in video_urls:
        print(f"🚀 Downloading video from: {url}")
        download_youtube_video(url, remove_audio=True)
        print("---")

    print("🎉 All downloads completed!")

if __name__ == "__main__":
    main()