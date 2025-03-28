import subprocess
import os
import random
import shutil
from pathlib import Path

def get_wav_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith('.wav')]

def get_audio_duration(wav_path):
    try:
        cmd = [
            'ffprobe', '-i', wav_path,
            '-show_entries', 'format=duration',
            '-v', 'quiet', '-of', 'csv=p=0'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None

def get_random_background(background_folder):
    video_files = [f for f in os.listdir(background_folder)
                   if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    if not video_files:
        raise FileNotFoundError("No video files found in background folder")
    return random.choice(video_files)

def trim_video(input_path, output_path, duration):
    try:
        cmd = [
            'ffprobe', '-i', input_path,
            '-show_entries', 'format=duration',
            '-v', 'quiet', '-of', 'csv=p=0'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        video_duration = float(result.stdout.strip())

        max_start = max(0, video_duration - duration)
        start_time = random.uniform(0, max_start) if max_start > 0 else 0

        print(f"Trimming video from {start_time:.2f}s for {duration:.2f}s duration")

        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy', '-y',
            output_path
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            print(f"FFmpeg Error Output:\n{process.stderr}")
            raise subprocess.CalledProcessError(process.returncode, cmd)

        print("✓ Video trimming complete")

    except Exception as e:
        print(f"Error trimming video: {e}")
        raise

def process_videos(background_folder, voiceovers_folder, subtitles_folder, final_folder):
    os.makedirs(final_folder, exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    wav_files = get_wav_files(voiceovers_folder)
    if not wav_files:
        print("No WAV files found in the Voiceovers folder.")
        return

    print(f"\nFound {len(wav_files)} WAV files to process.")
    processed_count = 0
    failed_count = 0

    for wav_file in wav_files:
        print(f"\n{'='*50}")
        print(f"Processing: {wav_file}")
        print(f"{'='*50}")

        base_name = os.path.splitext(wav_file)[0]
        wav_path = os.path.join(voiceovers_folder, wav_file)
        subtitle_src = os.path.join(subtitles_folder, f"{base_name}.ass")
        subtitle_dest = os.path.join(os.getcwd(), f"{base_name}.ass")
        output_path = os.path.join(final_folder, f"{base_name}.mp4")
        temp_video_path = os.path.join("temp", "trimmed.mp4")

        if not os.path.exists(subtitle_src):
            print(f"Subtitle file not found: {subtitle_src}. Skipping.")
            failed_count += 1
            continue

        try:
            # Copy subtitle to main folder
            shutil.copy(subtitle_src, subtitle_dest)
            print(f"✓ Copied subtitle to main folder: {subtitle_dest}")

            duration = get_audio_duration(wav_path)
            if not duration:
                print(f"Could not determine duration for {wav_file}. Skipping.")
                failed_count += 1
                continue

            background_file = get_random_background(background_folder)
            background_path = os.path.join(background_folder, background_file)
            print(f"Selected background video: {background_file}")

            print("Trimming background video...")
            trim_video(background_path, temp_video_path, duration)

            print("Adding subtitles and overlaying audio...")
            cmd = [
                'ffmpeg',
                '-i', temp_video_path,
                '-i', wav_path,
                '-vf', f'ass={base_name}.ass',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-y',
                output_path
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode != 0:
                print(f"FFmpeg Error Output:\n{process.stderr}")
                raise subprocess.CalledProcessError(process.returncode, cmd)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✓ Successfully created: {output_path}")
                processed_count += 1

                os.remove(wav_path)
                print(f"✓ Deleted WAV: {wav_path}")

                os.remove(subtitle_dest)
                print(f"✓ Deleted copied subtitle: {subtitle_dest}")

        except Exception as e:
            print(f"! Error processing {wav_file}: {e}")
            failed_count += 1
            if os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
            if os.path.exists(subtitle_dest):
                try:
                    os.remove(subtitle_dest)
                except:
                    pass
            continue

        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

    if os.path.exists("temp"):
        shutil.rmtree("temp")

    print(f"\n{'='*50}")
    print("Processing Complete!")
    print(f"{'='*50}")
    print(f"\nResults:")
    print(f"✓ Successfully processed: {processed_count}")
    print(f"✗ Failed: {failed_count}")

def verify_folders():
    required_folders = {
        "BackgroundVideos": "background videos",
        "Voiceovers": "WAV files",
        "Subtitles": "subtitle files",
        "FinalVideos": "output videos"
    }

    print("\nVerifying folders...")
    for folder, description in required_folders.items():
        if not os.path.exists(folder):
            print(f"Creating folder for {description}: {folder}")
            os.makedirs(folder)
        elif not os.access(folder, os.W_OK):
            raise PermissionError(f"No write access to {folder} folder")
        else:
            print(f"✓ {folder} folder exists and is accessible")

if __name__ == "__main__":
    try:
        print("\nVideo Processing Script")
        print("="*50)

        background_folder = "BackgroundVideos"
        voiceovers_folder = "Voiceovers"
        subtitles_folder = "Subtitles"
        final_folder = "FinalVideos"

        verify_folders()
        process_videos(background_folder, voiceovers_folder, subtitles_folder, final_folder)

    except Exception as e:
        print(f"\nFatal error: {e}")