import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_to_mp4(input_path, output_path):
    """
    Convert a video file to MP4 using FFmpeg.
    """
    command = [
        "ffmpeg",
        "-i", input_path,  # Input file
        "-c:v", "libx264",  # Encode video with H.264
        "-c:a", "aac",  # Encode audio with AAC
        "-y",  # Overwrite output file if it exists
        output_path  # Output file
    ]

    try:
        logging.info(f"🔄 Converting {input_path} to {output_path}")
        subprocess.run(command, check=True)
        logging.info(f"✅ Successfully converted: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error converting {input_path}: {e}")
        return False

def process_background_folder(background_folder):
    """
    Process all files in the background folder:
    - Skip files that are already in MP4 format.
    - Convert non-MP4 files to MP4.
    """
    if not os.path.exists(background_folder):
        logging.error(f"❌ Background folder not found: {background_folder}")
        return

    for filename in os.listdir(background_folder):
        input_path = os.path.join(background_folder, filename)
        
        # Skip directories
        if os.path.isdir(input_path):
            continue

        # Skip files that are already in MP4 format
        if filename.lower().endswith(".mp4"):
            logging.info(f"⏩ Skipping MP4 file: {filename}")
            continue

        # Generate output path
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(background_folder, f"{base_name}.mp4")

        # Convert non-MP4 files to MP4
        convert_to_mp4(input_path, output_path)

        # Optionally, delete the original file after conversion
        # os.remove(input_path)

if __name__ == "__main__":
    # Set the background folder path
    background_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BackgroundVideos")
    
    logging.info(f"🚀 Starting background video conversion in: {background_folder}")
    process_background_folder(background_folder)
    logging.info("✅ Conversion process completed")