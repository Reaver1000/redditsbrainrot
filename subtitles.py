import os
import csv
from force_alignment import *
from dict import *
import subprocess

def generate_subtitles(csv_path, voiceovers_folder, subtitles_folder):
    """
    Generate subtitles for each MP3 file in the Voiceovers folder.
    Clean up temporary WAV and text files after subtitles are generated.
    """
    # Ensure subtitles folder exists
    os.makedirs(subtitles_folder, exist_ok=True)

    # Get all MP3 files in the Voiceovers folder
    mp3_files = [f for f in os.listdir(voiceovers_folder) if f.lower().endswith(".mp3")]
    if not mp3_files:
        print("❌ No MP3 files found in the Voiceovers folder.")
        return

    # Read the CSV file
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header row

        # Create a list of rows (each row is a list of columns)
        csv_rows = list(reader)

    # Process each MP3 file
    for mp3_file in mp3_files:
        # Extract row number from the MP3 file name (e.g., "1.mp3" -> 1)
        try:
            row_number = int(os.path.splitext(mp3_file)[0])
        except ValueError:
            print(f"❌ Invalid MP3 filename: {mp3_file}. Expected format: '1.mp3', '2.mp3', etc.")
            continue

        # Skip if the row number is out of range
        if row_number < 1 or row_number > len(csv_rows):
            print(f"❌ Row {row_number} not found in the CSV file.")
            continue

        # Get title and content from the CSV (row_number - 1 because Python lists are zero-indexed)
        try:
            # Ensure the row number maps correctly to the CSV row
            csv_row = csv_rows[row_number - 2]  # row_number=1 -> csv_rows[0], row_number=2 -> csv_rows[1], etc.
            title, content = csv_row[1], csv_row[2]  # Columns B and C
        except IndexError:
            print(f"❌ Row {row_number} in the CSV file is missing data.")
            continue

        # Debugging: Print the row number and title being processed
        print(f"Processing {mp3_file} (Row {row_number}): {title}")

        # Define file paths
        mp3_path = os.path.join(voiceovers_folder, mp3_file)
        wav_path = os.path.join(voiceovers_folder, f"{row_number}.wav")
        txt_path = os.path.join(voiceovers_folder, f"{row_number}.txt")
        ass_path = os.path.join(subtitles_folder, f"{row_number}.ass")

        # Step 1: Convert MP3 to WAV for force alignment
        convert_mp3_to_wav(mp3_path, wav_path)

        # Step 2: Format the text and write it to the temporary text file
        formatted_text = format_text(f"{title}\n\n{content}")  # Format the text
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(formatted_text)  # Write formatted text to the text file
        

        # Step 3: Perform force alignment
        try:
            bundle, waveform, labels, emission1 = class_label_prob(wav_path)
            trellis, emission, tokens = trellis_algo(labels, formatted_text, emission1)  # Use formatted_text
            path = backtrack(trellis, emission, tokens)
            segments = merge_repeats(path, formatted_text)  # Use formatted_text
            word_segments = merge_words(segments)

            # Step 4: Generate timing list
            timing_list = []
            for i in range(len(word_segments)):
                timing_list.append(display_segment(bundle, trellis, word_segments, waveform, i))

            # Step 5: Convert timing list to ASS file
            convert_timing_to_ass(timing_list, ass_path)
            print(f"✅ Subtitles generated: {ass_path}")

        except Exception as e:
            print(f"❌ Error during force alignment for {mp3_file}: {e}")
            continue

        # Step 6: Clean up temporary WAV and text files
        os.remove(wav_path)
        os.remove(txt_path)
        print(f"🧹 Cleaned up temporary files: {wav_path}, {txt_path}")

def convert_mp3_to_wav(mp3_path, wav_path):
    """
    Convert MP3 to WAV (16kHz, 16-bit, mono) for force alignment.
    """
    command = [
        'ffmpeg',
        '-i', mp3_path,  # Input MP3 file
        '-ac', '1',  # Mono
        '-ar', '16000',  # 16kHz sample rate
        '-sample_fmt', 's16',  # 16-bit
        wav_path  # Output WAV file
    ]
    subprocess.run(command, check=True)
    print(f"✅ Converted {mp3_path} to {wav_path}")

if __name__ == "__main__":
    # Define paths
    csv_path = "reddit_posts.csv"  # Path to the CSV file
    voiceovers_folder = "Voiceovers"  # Folder containing MP3 files
    subtitles_folder = "Subtitles"  # Folder to save subtitle files

    # Generate subtitles
    generate_subtitles(csv_path, voiceovers_folder, subtitles_folder)