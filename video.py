import subprocess
import os
import random
import shutil  # For copying files

def get_mp3_files(voiceovers_folder):
    """
    Get a list of MP3 files in the Voiceovers folder.
    """
    mp3_files = [f for f in os.listdir(voiceovers_folder) if f.lower().endswith(".mp3")]
    return mp3_files

def get_random_background(background_folder):
    """
    Get a random background video from the BackgroundVideos folder.
    """
    background_files = [f for f in os.listdir(background_folder) if f.lower().endswith(".mp4")]
    if not background_files:
        raise FileNotFoundError("No background videos found in the BackgroundVideos folder.")
    return random.choice(background_files)

def get_audio_duration(audio_path):
    """
    Get the duration of an audio file using ffprobe.
    """
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def get_video_duration(video_path):
    """
    Get the duration of a video file using ffprobe.
    """
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def trim_video(input_path, output_path, duration):
    """
    Extract a segment of the video starting at a random point.
    """
    # Get the duration of the background video
    background_duration = get_video_duration(input_path)

    # Calculate the maximum start time to ensure the segment fits
    max_start_time = background_duration - duration
    if max_start_time < 0:
        raise ValueError(f"Background video is too short ({background_duration:.2f}s) to fit the MP3 ({duration:.2f}s).")

    # Generate a random start time
    start_time = random.uniform(0, max_start_time)
    print(f"Extracting video segment from {start_time:.2f}s to {start_time + duration:.2f}s")

    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', str(start_time),
        '-t', str(duration),
        '-c', 'copy',
        output_path
    ]
    subprocess.run(command, check=True)
    print(f"✅ Extracted video segment saved: {output_path}")

def add_subtitles_and_overlay_audio(video_path, audio_path, subtitles_path, output_path):
    """
    Add subtitles and overlay audio to the video.
    """
    # Copy the subtitle file to the main folder (temporarily)
    temp_subtitles_path = os.path.basename(subtitles_path)  # e.g., "10.ass"
    shutil.copy(subtitles_path, temp_subtitles_path)

    # Copy the MP3 file to the main folder (temporarily)
    temp_audio_path = os.path.basename(audio_path)  # e.g., "10.mp3"
    shutil.copy(audio_path, temp_audio_path)

    try:
        # Use the temporary subtitle and MP3 files in the main folder
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', temp_audio_path,  # Use the temporary MP3 file
            '-vf', f"subtitles='{temp_subtitles_path}'",  # Use the temporary subtitle file
            '-c:v', 'libx264',
            '-map', '0:v',
            '-map', '1:a',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-shortest',
            output_path
        ]
        subprocess.run(command, check=True)
        print(f"✅ Final video saved: {output_path}")
    finally:
        # Clean up: Delete the temporary files
        if os.path.exists(temp_subtitles_path):
            os.remove(temp_subtitles_path)
            print(f"🗑️ Deleted temporary subtitle file: {temp_subtitles_path}")
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"🗑️ Deleted temporary MP3 file: {temp_audio_path}")

def process_videos(background_folder, voiceovers_folder, subtitles_folder, final_folder):
    """
    Process all MP3 files in the Voiceovers folder.
    """
    # Ensure final folder exists
    os.makedirs(final_folder, exist_ok=True)

    # Get list of MP3 files
    mp3_files = get_mp3_files(voiceovers_folder)
    if not mp3_files:
        print("❌ No MP3 files found in the Voiceovers folder.")
        return

    # Process each MP3 file
    for mp3_file in mp3_files:
        # Define file paths
        mp3_path = os.path.join(voiceovers_folder, mp3_file)  # MP3 file in Voiceovers folder

        # Construct the subtitle file path
        base_name = os.path.splitext(mp3_file)[0]  # e.g., "10" from "10.mp3"
        subtitles_path = os.path.join(subtitles_folder, f"{base_name}.ass")  # e.g., "Subtitles\10.ass"

        # Debugging: Print the subtitle path to verify
        print(f"Looking for subtitles: {subtitles_path}")

        # Check if the subtitle file exists
        if not os.path.exists(subtitles_path):
            print(f"❌ Subtitle file not found: {subtitles_path}. Skipping this MP3 file.")
            continue

        # Define the output video path
        output_path = os.path.join(final_folder, f"{base_name}_final.mp4")

        # Get the duration of the MP3 file
        duration = get_audio_duration(mp3_path)
        print(f"Processing {mp3_file} (Duration: {duration:.2f} seconds)")

        # Get a random background video
        background_file = get_random_background(background_folder)
        background_path = os.path.join(background_folder, background_file)

        # Extract a segment from the background video
        trimmed_video = os.path.join(final_folder, "trimmed.mp4")
        trim_video(background_path, trimmed_video, duration)

        # Add subtitles and overlay audio
        add_subtitles_and_overlay_audio(trimmed_video, mp3_path, subtitles_path, output_path)

        # Clean up the trimmed video (optional)
        os.remove(trimmed_video)

if __name__ == "__main__":
    # Define folder paths
    background_folder = "BackgroundVideos"  # Folder for background videos
    voiceovers_folder = "Voiceovers"  # Folder for MP3 files
    subtitles_folder = "Subtitles"  # Folder for subtitle files
    final_folder = "FinalVideos"  # Folder for final output videos

    # Process all MP3 files
    process_videos(background_folder, voiceovers_folder, subtitles_folder, final_folder)