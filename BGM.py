import os
import random
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def get_audio_duration(audio_path):
    """
    Get the duration of an audio file using ffprobe
    """
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout.strip():
            return float(result.stdout.strip())
        else:
            print(f"Could not get duration for: {audio_path}")
            return None
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None

def create_bgm_mix(tts_path, output_path=None, bgm_folder='BackgroundMusic', bgm_volume=0.45, archive_mode='delete'):
    """
    Create a mixed audio file with TTS overlaid on looped background music
    archive_mode: 'delete' to remove original files (default), 'move' to archive them
    """
    print(f"Creating BGM mix for: {tts_path}")

    # Validate TTS file exists
    if not os.path.exists(tts_path):
        print(f"TTS file not found: {tts_path}")
        return None

    # Generate output path if not provided - now using the same filename
    if output_path is None:
        tts_path = Path(tts_path)
        temp_output_path = tts_path.parent / f"temp_{tts_path.name}"
    else:
        temp_output_path = Path(output_path)

    # Find all music files
    music_files = [
        f for f in os.listdir(bgm_folder)
        if f.lower().endswith(('.mp3', '.wav', '.m4a'))
    ]

    if not music_files:
        print("No background music files found in BackgroundMusic folder")
        return None

    # Randomly select a music file
    selected_music = os.path.join(bgm_folder, random.choice(music_files))
    print(f"Selected BGM: {os.path.basename(selected_music)}")

    # Get TTS duration
    tts_duration = get_audio_duration(tts_path)
    if not tts_duration:
        return None

    try:
        # First, normalize the TTS audio
        temp_tts = str(temp_output_path).replace('.wav', '_temp_tts.wav')
        normalize_command = [
            'ffmpeg',
            '-i', tts_path,
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
            '-ar', '44100',
            '-ac', '2',
            temp_tts
        ]
        subprocess.run(normalize_command, check=True)

        # Then, create looped BGM at higher volume (45%)
        temp_bgm = str(temp_output_path).replace('.wav', '_temp_bgm.wav')
        bgm_command = [
            'ffmpeg',
            '-stream_loop', '-1',
            '-i', selected_music,
            '-t', str(tts_duration),
            '-af', f'volume={bgm_volume}',
            '-ar', '44100',
            '-ac', '2',
            temp_bgm
        ]
        subprocess.run(bgm_command, check=True)

        # Finally, mix them together
        mix_command = [
            'ffmpeg',
            '-i', temp_tts,
            '-i', temp_bgm,
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:weights=1.7 1[aout]',
            '-map', '[aout]',
            '-ar', '44100',
            '-ac', '2',
            str(temp_output_path)
        ]
        subprocess.run(mix_command, check=True)

        # Clean up temporary files
        os.remove(temp_tts)
        os.remove(temp_bgm)

        # Handle the original file based on archive_mode
        if archive_mode == 'move':
            # Create archive folder if it doesn't exist
            archive_folder = os.path.join('Voiceovers', 'processed_files')
            os.makedirs(archive_folder, exist_ok=True)

            # Move the original file to archive
            archive_path = os.path.join(archive_folder, tts_path.name)
            shutil.move(tts_path, archive_path)
            print(f"Moved original file to archive: {tts_path.name}")
        else:  # Default 'delete' mode
            os.remove(tts_path)
            print(f"Deleted original file: {tts_path.name}")

        # Rename the temp output file to the original filename
        shutil.move(str(temp_output_path), str(tts_path))
        print(f"Mixed audio saved as: {tts_path.name}")
        return str(tts_path)

    except subprocess.CalledProcessError as e:
        print(f"Error mixing audio: {e}")
        # Clean up any temporary files that might exist
        if os.path.exists(temp_tts):
            os.remove(temp_tts)
        if os.path.exists(temp_bgm):
            os.remove(temp_bgm)
        if os.path.exists(str(temp_output_path)):
            os.remove(str(temp_output_path))
        return None

def main():
    """
    Process WAV files with BGM mixing
    """
    if os.path.exists('Voiceovers'):
        # Only process WAV files that don't start with 'temp_'
        wav_files = [f for f in os.listdir('Voiceovers')
                    if f.endswith('.wav') and not f.startswith('temp_')]

        if wav_files:
            print(f"Found {len(wav_files)} WAV files to process")
            for wav_file in wav_files:
                test_file = os.path.join('Voiceovers', wav_file)
                create_bgm_mix(test_file)  # Uses default 'delete' mode
        else:
            print("No WAV files found in Voiceovers folder")
    else:
        print("Voiceovers folder not found")

if __name__ == "__main__":
    main()