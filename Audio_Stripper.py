import os
import subprocess
from pathlib import Path

def remove_audio_ffmpeg(input_video: str, output_video: str):
    """
    Removes audio from a video using FFmpeg.

    Args:
        input_video (str): Path to the input video file.
        output_video (str): Path to save the output video (without audio).
    """
    # Ensure the output file doesn't already exist
    if Path(output_video).exists():
        print(f"⚠️ Output file already exists: {output_video}")
        return

    command = [
        "ffmpeg",
        "-i", input_video,  # Input video file
        "-c:v", "copy",     # Copy video stream without re-encoding
        "-an",              # Remove audio
        output_video        # Output video file
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ Audio removed: {output_video}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error removing audio: {e}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please ensure FFmpeg is installed and added to your PATH.")
        return False

def remove_audio_from_directory(directory: str):
    """
    Removes audio from all video files in a directory and deletes the original files.
    Skips files that already have "_no_audio" in their names.

    Args:
        directory (str): Path to the directory containing video files.
    """
    print(f"🔍 Processing directory: {directory}")

    # Process each video file in the directory
    for filename in os.listdir(directory):
        print(f"🔎 Found file: {filename}")

        # Skip files that already have "_no_audio" in their names
        if "_no_audio" in filename:
            print(f"⏩ Skipping (already processed): {filename}")
            continue

        # Check for supported video formats
        if filename.endswith((".mp4", ".webm", ".mkv")):
            input_video = os.path.join(directory, filename)
            output_video = os.path.join(directory, f"{Path(filename).stem}_no_audio{Path(filename).suffix}")

            print(f"🛠️ Processing: {input_video} -> {output_video}")

            # Remove audio and delete the original file if successful
            if remove_audio_ffmpeg(input_video, output_video):
                try:
                    os.remove(input_video)
                    print(f"🗑️ Deleted original file: {input_video}")
                except OSError as e:
                    print(f"❌ Error deleting file {input_video}: {e}")
        else:
            print(f"⏩ Skipping (unsupported format): {filename}")

def main():
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Remove audio from all video files in the current directory and delete the originals. Skips files that already have '_no_audio' in their names.")
    parser.add_argument("directory", nargs="?", default=".", help="Path to the directory containing video files (default: current directory).")
    args = parser.parse_args()

    # Check if the input is a directory
    if os.path.isdir(args.directory):
        remove_audio_from_directory(args.directory)
    else:
        print(f"❌ Invalid input: {args.directory} is not a directory.")

if __name__ == "__main__":
    main()