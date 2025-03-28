import os
import csv
from pydub import AudioSegment

def format_time(seconds):
    """Format time in seconds to ASS subtitle format (h:mm:ss.cs)"""
    milliseconds = int(seconds * 100)
    hours = milliseconds // 360000
    minutes = (milliseconds % 360000) // 6000
    seconds = (milliseconds % 6000) // 100
    centiseconds = milliseconds % 100
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"

def split_into_bark_chunks(text, max_chunk_size=200):
    """Split text into chunks using Bark's logic"""
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    current_pos = 0
    text_length = len(text)

    while current_pos < text_length:
        end_pos = min(current_pos + max_chunk_size, text_length)

        if end_pos < text_length:
            last_period = text.rfind('. ', current_pos, end_pos)
            last_exclaim = text.rfind('! ', current_pos, end_pos)
            last_question = text.rfind('? ', current_pos, end_pos)

            sentence_end = max(last_period, last_exclaim, last_question)

            if sentence_end != -1 and sentence_end > current_pos:
                end_pos = sentence_end + 1
            else:
                last_space = text.rfind(' ', current_pos, end_pos)
                if last_space != -1:
                    end_pos = last_space + 1

        chunk = text[current_pos:end_pos].strip()
        if chunk:
            chunks.append(chunk)
        current_pos = end_pos

    return chunks

def split_chunk_into_words(chunk, max_words_per_line=2):
    """Split a chunk into groups of 1-2 words"""
    words = chunk.split()
    word_groups = []
    for i in range(0, len(words), max_words_per_line):
        group = " ".join(words[i:i + max_words_per_line])
        word_groups.append(group)
    return word_groups

def generate_subtitles(csv_path, voiceovers_folder, subtitles_folder):
    """Generate subtitles for each WAV file using Bark chunks and word-by-word display"""
    os.makedirs(subtitles_folder, exist_ok=True)

    wav_files = [f for f in os.listdir(voiceovers_folder) if f.lower().endswith('.wav')]
    if not wav_files:
        print("❌ No WAV files found in the Voiceovers folder.")
        return

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        csv_rows = list(reader)

    for wav_file in wav_files:
        filename_without_ext = os.path.splitext(wav_file)[0]
        matching_row = next((row for row in csv_rows if row['File Name'] == filename_without_ext), None)

        if not matching_row:
            print(f"❌ No matching row found for {wav_file}")
            continue

        title = matching_row['Title']
        content = matching_row['Post Content']
        full_text = f"{title}. {content}"

        print(f"Processing {wav_file}: {title}")

        wav_path = os.path.join(voiceovers_folder, wav_file)
        ass_path = os.path.join(subtitles_folder, f"{filename_without_ext}.ass")

        try:
            # Get audio duration using pydub
            audio = AudioSegment.from_file(wav_path)
            duration = len(audio) / 1000.0  # Convert milliseconds to seconds

            # First split into Bark chunks
            bark_chunks = split_into_bark_chunks(full_text)

            # Calculate time per character for each Bark chunk
            total_chars = sum(len(chunk) for chunk in bark_chunks)
            time_per_char = duration / total_chars

            ass_header = """[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,150,150,0,0,1,3,3,5,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            ass_content = ass_header

            current_time = 0.0
            for bark_chunk in bark_chunks:
                # Calculate time for this Bark chunk
                chunk_duration = len(bark_chunk) * time_per_char

                # Split the Bark chunk into word groups
                word_groups = split_chunk_into_words(bark_chunk)

                # Calculate time per word group within this chunk
                time_per_group = chunk_duration / len(word_groups)

                # Generate subtitles for each word group
                for word_group in word_groups:
                    end_time = current_time + time_per_group
                    ass_content += f"Dialogue: 0,{format_time(current_time)},{format_time(end_time)},Default,,0,0,0,,{word_group}\n"
                    current_time = end_time

            # Write the ASS file
            with open(ass_path, 'w', encoding='utf-8-sig') as f:
                f.write(ass_content)

            print(f"✅ Subtitles generated: {ass_path}")

        except Exception as e:
            print(f"❌ Error during subtitle generation for {wav_file}: {str(e)}")
            continue

if __name__ == "__main__":
    csv_path = "reddit_posts.csv"
    voiceovers_folder = "voiceovers"
    subtitles_folder = "subtitles"
    generate_subtitles(csv_path, voiceovers_folder, subtitles_folder)