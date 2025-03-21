import os
import random
import subprocess
import logging
import shlex

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_audio_duration(audio_path):
    """
    Get the duration of an audio file using ffprobe.
    """
    if not os.path.exists(audio_path):
        logging.error(f"❌ Audio file not found: {audio_path}")
        return None
        
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    try:
        duration = float(subprocess.check_output(command).decode().strip())
        logging.info(f"📊 Audio duration: {duration}s for {audio_path}")
        return duration
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error getting audio duration: {e}")
        return None

def trim_and_attach_audio(background_video, mp3_path, output_video, start_time, duration):
    """
    Trim the background video and attach the audio.
    """
    command = [
        "ffmpeg",
        "-i", background_video,  # Input background video
        "-i", mp3_path,  # Input audio
        "-ss", str(start_time),  # Start time for trimming
        "-t", str(duration),  # Duration of the trimmed video
        "-c:v", "libx264",  # Encode video stream
        "-c:a", "copy",  # Copy audio stream (no re-encoding)
        "-y",  # Overwrite output file if it exists
        output_video  # Output video
    ]

    try:
        logging.info(f"🔄 Trimming video and attaching audio: {output_video}")
        logging.info(f"🔧 Running command: {' '.join(command)}")
        
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        # Add a timeout to prevent hanging
        stdout, stderr = process.communicate(timeout=600)
        
        if process.returncode == 0:
            logging.info(f"✅ Successfully created: {output_video}")
            return True
        else:
            logging.error(f"❌ FFmpeg error (code {process.returncode}):")
            logging.error(stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("❌ FFmpeg command timed out after 10 minutes.")
        process.kill()  # Terminate the hanging process
        stdout, stderr = process.communicate()  # Capture any remaining output
        logging.error(stderr)
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return False

def add_subtitles(input_video, ass_path, output_video):
    """
    Add ASS format subtitles to the video.
    """
    # Convert the subtitle path to an absolute path and escape it properly
    subtitle_path = os.path.abspath(ass_path)
    
    # On Windows, ffmpeg has issues with paths containing backslashes and quotes
    # Use the ass filter with proper escaping
    if os.name == 'nt':  # Windows
        # Escape the path for Windows
        subtitle_path = subtitle_path.replace('\\', '\\\\')
        subtitle_filter = f"ass={subtitle_path}"
    else:
        # For Unix systems, escape spaces and special characters
        subtitle_path = subtitle_path.replace(':', '\\:').replace(' ', '\\ ')
        subtitle_filter = f"ass={subtitle_path}"
    
    command = [
        "ffmpeg",
        "-i", input_video,  # Input video
        "-vf", subtitle_filter,  # Add subtitles
        "-c:v", "libx264",  # Re-encode video stream
        "-c:a", "copy",  # Copy audio stream (no re-encoding)
        "-y",  # Overwrite output file if it exists
        output_video  # Output video
    ]

    try:
        logging.info(f"🔄 Adding ASS subtitles: {output_video}")
        logging.info(f"🔧 Running command: {' '.join(command)}")
        
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logging.info(f"✅ Successfully created: {output_video}")
            return True
        else:
            logging.error(f"❌ FFmpeg error (code {process.returncode}):")
            logging.error(stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return False

def process_video_audio_subtitles(background_video, mp3_path, ass_path, output_video):
    """
    Process video, audio, and subtitles in two steps:
    1. Trim video and attach audio.
    2. Add subtitles.
    """
    # Check if all input files exist
    if not os.path.exists(background_video):
        logging.error(f"❌ Background video not found: {background_video}")
        return
        
    if not os.path.exists(mp3_path):
        logging.error(f"❌ Audio file not found: {mp3_path}")
        return
        
    if not os.path.exists(ass_path):
        logging.error(f"❌ Subtitle file not found: {ass_path}")
        return

    # Get the duration of the audio file
    audio_duration = get_audio_duration(mp3_path)
    if not audio_duration:
        return

    # Get the duration of the background video
    bg_duration = get_audio_duration(background_video)
    if not bg_duration:
        return
        
    if bg_duration < audio_duration:
        logging.error(f"❌ Background video is too short ({bg_duration}s < {audio_duration}s)")
        return

    # Calculate a random start time for trimming
    max_start = bg_duration - audio_duration
    start_time = random.uniform(0, max_start)
    logging.info(f"🎬 Using start time: {start_time:.2f}s for background video")

    # Step 1: Trim video and attach audio
    intermediate_video = output_video.replace(".mp4", "_intermediate.mp4")
    if not trim_and_attach_audio(background_video, mp3_path, intermediate_video, start_time, audio_duration):
        return

    # Step 2: Add subtitles
    if not add_subtitles(intermediate_video, ass_path, output_video):
        logging.warning("⚠️ Subtitle processing failed. Keeping video without subtitles.")
        # If subtitles fail, rename the intermediate file to the final output
        os.rename(intermediate_video, output_video)
    else:
        # Clean up the intermediate file
        os.remove(intermediate_video)

def get_files_to_process(voiceovers_folder, final_videos_folder):
    """
    Get pairs of MP3 and ASS files from the Voiceovers folder.
    Skip files that already have a corresponding MP4 in the FinalVideos folder.
    Returns a list of tuples: [(mp3_path, ass_path, output_path), ...]
    """
    if not os.path.exists(voiceovers_folder):
        logging.error(f"❌ Voiceovers folder not found: {voiceovers_folder}")
        return []
        
    logging.info(f"🔍 Scanning for MP3/ASS pairs in: {voiceovers_folder}")
    
    files_to_process = []
    for file in os.listdir(voiceovers_folder):
        if file.lower().endswith(".mp3"):  # Case-insensitive check
            mp3_path = os.path.join(voiceovers_folder, file)
            
            # Extract base name without extension
            base_name = os.path.splitext(file)[0]
            ass_path = os.path.join(voiceovers_folder, f"{base_name}.ass")
            
            # Check for case variations of .ass extension
            if not os.path.exists(ass_path):
                for ext in [".ass", ".ASS", ".Ass"]:
                    test_path = os.path.join(voiceovers_folder, f"{base_name}{ext}")
                    if os.path.exists(test_path):
                        ass_path = test_path
                        break

            # Check if the ASS file exists
            if not os.path.exists(ass_path):
                logging.warning(f"❌ No matching ASS file found for {file}")
                continue

            # Make sure output filename is correct (doesn't double the extension)
            output_filename = f"{base_name}.mp4"
            output_path = os.path.join(final_videos_folder, output_filename)

            # Skip if the output file already exists
            if os.path.exists(output_path):
                logging.info(f"⏩ Skipping {file} (output already exists)")
                continue

            files_to_process.append((mp3_path, ass_path, output_path))
            logging.info(f"✅ Found pair: {mp3_path} and {ass_path} → {output_path}")
            
    logging.info(f"📊 Total MP3/ASS pairs found: {len(files_to_process)}")
    return files_to_process

def main(debug_mode=True):
    # Use absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    voiceovers_folder = os.path.join(base_dir, "Voiceovers")
    background_videos_folder = os.path.join(base_dir, "BackgroundVideos")
    output_folder = os.path.join(base_dir, "FinalVideos")
    
    logging.info(f"📂 Voiceovers folder: {voiceovers_folder}")
    logging.info(f"📂 Background videos folder: {background_videos_folder}")
    logging.info(f"📂 Output folder: {output_folder}")

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get all MP3 and ASS files to process
    files_to_process = get_files_to_process(voiceovers_folder, output_folder)
    if not files_to_process:
        logging.error("❌ No MP3 and ASS file pairs found in the Voiceovers folder.")
        return

    # Get all background videos
    if not os.path.exists(background_videos_folder):
        logging.error(f"❌ Background videos folder not found: {background_videos_folder}")
        return
        
    background_videos = [os.path.join(background_videos_folder, f) for f in os.listdir(background_videos_folder) 
                        if f.lower().endswith((".mp4", ".webm", ".mkv", ".avi"))]
                        
    if not background_videos:
        logging.error("❌ No background videos found in the BackgroundVideos folder.")
        return
        
    logging.info(f"📊 Found {len(background_videos)} background videos")

    # Debug mode: Process only the first file
    if debug_mode:
        files_to_process = [files_to_process[0]]  # Process only the first file
        logging.info("🔧 Debug mode: Processing only the first file.")

    # Process each MP3 and ASS file
    for mp3_path, ass_path, output_path in files_to_process:
        # Choose a random background video
        background_video_path = random.choice(background_videos)
        logging.info(f"🎬 Selected background video: {background_video_path}")

        # Process the video, audio, and subtitles in two steps
        process_video_audio_subtitles(background_video_path, mp3_path, ass_path, output_path)

if __name__ == "__main__":
    logging.info("🚀 Starting video processing script")
    # Keep debug_mode=True as requested
    main(debug_mode=True)
    logging.info("✅ Script execution completed")