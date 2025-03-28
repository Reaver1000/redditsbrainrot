import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_to_mp4(input_path, output_path):
    """
    Convert a video file to MP4 using FFmpeg, preserving audio.
    """
    logging.info(f"🕒 Converting {os.path.basename(input_path)} to MP4. This may take some time...")
    
    command = [
        "ffmpeg",
        "-i", input_path,  # Input file
        "-c:v", "libx264",  # Encode video with H.264
        "-c:a", "copy",     # Copy audio without re-encoding
        "-y",               # Overwrite output file if it exists
        output_path         # Output file
    ]

    try:
        subprocess.run(command, check=True)
        logging.info(f"✅ Successfully converted: {os.path.basename(output_path)}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error converting {os.path.basename(input_path)}: {e}")
        return False

def process_background_folder(background_folder):
    """
    Process all files in the background folder:
    - Convert non-MP4 files to MP4
    - Delete original non-MP4 files
    """
    if not os.path.exists(background_folder):
        logging.error(f"❌ Background folder not found: {background_folder}")
        return

    # Get list of non-MP4 files first
    non_mp4_files = [
        f for f in os.listdir(background_folder) 
        if os.path.isfile(os.path.join(background_folder, f)) 
        and not f.lower().endswith('.mp4')
    ]

    if not non_mp4_files:
        logging.info("✅ No non-MP4 files found to convert.")
        return

    logging.info(f"🚀 Found {len(non_mp4_files)} files to convert. This process may take several minutes.")

    converted_count = 0
    for filename in non_mp4_files:
        input_path = os.path.join(background_folder, filename)
        
        # Generate output path
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(background_folder, f"{base_name}.mp4")

        # Convert non-MP4 files to MP4
        if convert_to_mp4(input_path, output_path):
            # Delete the original file
            try:
                os.remove(input_path)
                logging.info(f"🗑️ Deleted original file: {filename}")
                converted_count += 1
            except Exception as e:
                logging.error(f"❌ Error deleting {filename}: {e}")

    logging.info(f"✅ Conversion complete. {converted_count} files converted and original files removed.")

def main():
    # Set the background folder path
    background_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BackgroundVideos")
    
    logging.info(f"🚀 Starting background video conversion in: {background_folder}")
    process_background_folder(background_folder)
    logging.info("🎉 Conversion process completed")

if __name__ == "__main__":
    main()