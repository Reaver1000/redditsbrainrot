import os
import csv
from pydub import AudioSegment

# Function to convert milliseconds to ASS time format (h:mm:ss.cc)
def milliseconds_to_ass_time(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    centiseconds = milliseconds // 10  # ASS uses centiseconds (1/100 of a second)
    return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}.{int(centiseconds):02}"

# Function to split text into 1-3 word blocks
def split_text_into_blocks(text):
    words = text.split()  # Split text into individual words
    blocks = []
    current_block = []

    for word in words:
        current_block.append(word)
        # Create a block of 1-3 words
        if len(current_block) >= 3 or word[-1] in ".!?":  # End block at punctuation or after 3 words
            blocks.append(" ".join(current_block))
            current_block = []

    # Add any remaining words as a final block
    if current_block:
        blocks.append(" ".join(current_block))
    return blocks

# Function to generate ASS content
def generate_ass(text, audio_duration):
    blocks = split_text_into_blocks(text)  # Split text into 1-3 word blocks
    
    # ASS file header
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    ass_content = [ass_header]
    start_time = 0
    duration_per_block = audio_duration // len(blocks)

    for block in blocks:
        end_time = start_time + duration_per_block
        # ASS event line format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        ass_line = f"Dialogue: 0,{milliseconds_to_ass_time(start_time)},{milliseconds_to_ass_time(end_time)},Default,,0,0,0,,{block}\n"
        ass_content.append(ass_line)
        start_time = end_time + 10  # Add a small gap between subtitles

    return "".join(ass_content)

# Directory containing mp3 files
voiceovers_dir = "Voiceovers"

# Check if the directory exists
if not os.path.exists(voiceovers_dir):
    print(f"Directory '{voiceovers_dir}' does not exist.")
    exit()

# Load the CSV file
csv_file = "reddit_posts.csv"
if not os.path.exists(csv_file):
    print(f"CSV file '{csv_file}' does not exist.")
    exit()

# Read the CSV file into a list of rows
with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    rows = list(reader)  # Convert the CSV reader object to a list of rows

# Process each mp3 file in the Voiceovers directory
for mp3_file in os.listdir(voiceovers_dir):
    if mp3_file.endswith(".mp3"):
        file_number = mp3_file.split('.')[0]  # Extract the number from the filename
        ass_file = os.path.join(voiceovers_dir, f"{file_number}.ass")

        # Skip if ASS file already exists
        if os.path.exists(ass_file):
            print(f"ASS file for {mp3_file} already exists. Skipping.")
            continue

        # Convert file number to row index (CSV rows are 0-indexed, and the first row is the header)
        try:
            row_index = int(file_number)  # File number corresponds to row number
            if row_index < 1 or row_index >= len(rows):
                print(f"Row {row_index} does not exist in the CSV for {mp3_file}. Skipping.")
                continue
        except ValueError:
            print(f"Invalid file number '{file_number}' in {mp3_file}. Skipping.")
            continue

        # Get the text from columns B and C (index 1 and 2 in the row)
        title = rows[row_index][1]  # Column B (Title)
        post_content = rows[row_index][2]  # Column C (Post Content)
        text = f"{title}. {post_content}"

        # Load the mp3 file to calculate its duration
        mp3_path = os.path.join(voiceovers_dir, mp3_file)
        audio = AudioSegment.from_mp3(mp3_path)
        audio_duration = len(audio)  # Duration in milliseconds

        # Generate ASS content
        ass_content = generate_ass(text, audio_duration)

        # Save the ASS file
        with open(ass_file, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        print(f"Created ASS file for {mp3_file}.")