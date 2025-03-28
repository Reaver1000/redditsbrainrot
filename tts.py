import os
import sys
import re
import random
import torch
import pandas as pd
import numpy as np
from scipy.io.wavfile import write
from bark import generate_audio, SAMPLE_RATE, preload_models
import traceback
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tts_log.txt"),
        logging.StreamHandler()
    ]
)

class TTSGenerator:
    def __init__(self, voice_preset=None, text_temp=0.7, waveform_temp=0.7):
        """
        Initialize TTS Generator with optional voice preset and temperature settings.
        """
        self.voice_preset = voice_preset
        self.sample_rate = SAMPLE_RATE
        self.models_loaded = False
        self.text_temp = text_temp  # Store text temperature
        self.waveform_temp = waveform_temp  # Store waveform temperature

    def initialize_models(self):
        """
        Load the required models
        """
        try:
            logging.info("Loading TTS models...")
            # The fix needs to be applied within the bark library.
            try:
                import bark.generation
                original_torch_load = bark.generation.torch.load  # Store the original torch.load
                def _safe_torch_load(ckpt_path, map_location, weights_only=False):
                    return original_torch_load(ckpt_path, map_location=map_location, weights_only=weights_only)
                bark.generation.torch.load = _safe_torch_load  # Patch
                preload_models()
            except Exception as e:
                logging.error(f"Failed to apply torch.load patch: {e}")
                raise e

            self.models_loaded = True
            logging.info("TTS models loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to load TTS models: {str(e)}")
            traceback.print_exc()
            return False

    def generate_speech(self, text, output_path):
        """
        Generate speech from text and save to output_path
        """
        if not self.models_loaded:
            if not self.initialize_models():
                return False

        try:
            logging.info(f"Generating speech for text of length {len(text)} characters")

            # Split text into chunks if it's too long
            max_chunk_size = 200  # Adjust based on your needs
            chunks = self._split_text_into_chunks(text, max_chunk_size)

            # Generate audio for each chunk
            audio_arrays = []
            for i, chunk in enumerate(chunks):
                logging.info(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} characters")

                # Use torch.amp.autocast instead of torch.cuda.amp.autocast
                with torch.amp.autocast('cuda' if torch.cuda.is_available() else 'cpu'):
                    audio_array = generate_audio(
                        chunk,
                        history_prompt=self.voice_preset,
                        text_temp=self.text_temp,
                        waveform_temp=self.waveform_temp
                    )
                    # Convert each chunk to float32 immediately after generation
                    audio_array = audio_array.astype(np.float32)
                audio_arrays.append(audio_array)

            # Concatenate all audio arrays
            combined_audio = np.concatenate(audio_arrays)

            # Normalize audio to range [-1, 1]
            if np.max(np.abs(combined_audio)) > 0:
                combined_audio = combined_audio / np.max(np.abs(combined_audio))

            try:
                # Try using soundfile first (better handling of different formats)
                import soundfile as sf
                sf.write(output_path, combined_audio, self.sample_rate)
            except ImportError:
                # Fallback to scipy if soundfile is not available
                write(output_path, self.sample_rate, combined_audio)

            logging.info(f"Speech generated and saved to {output_path}")
            return True

        except Exception as e:
            logging.error(f"Error generating speech: {str(e)}")
            traceback.print_exc()
            return False

    def _split_text_into_chunks(self, text, max_chunk_size):
        """
        Split text into chunks of max_chunk_size characters
        Try to split at sentence boundaries
        """
        # If text is short enough, return as is
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Find the end position for this chunk
            end_pos = min(current_pos + max_chunk_size, len(text))

            # If we're not at the end of the text, try to find a sentence boundary
            if end_pos < len(text):
                # Look for sentence endings (.!?) followed by a space or newline
                sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s', text[current_pos:end_pos])]

                if sentence_endings:
                    # Use the last sentence ending found
                    end_pos = current_pos + sentence_endings[-1]
                else:
                    # If no sentence ending, look for the last space
                    last_space = text[current_pos:end_pos].rfind(' ')
                    if last_space > 0:
                        end_pos = current_pos + last_space + 1

            # Add the chunk to our list
            chunks.append(text[current_pos:end_pos].strip())
            current_pos = end_pos

        return chunks

def process_csv(csv_path='reddit_posts.csv', output_dir='voiceovers'):
    """
    Process all unprocessed rows in the CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Get a list of all .npz files in the history_prompts folder
        history_prompts_dir = "history_prompts"
        npz_files = [f for f in os.listdir(history_prompts_dir) if f.endswith('.npz')]

        if not npz_files:
            logging.error("No .npz files found in the history_prompts folder")
            return

        # Read CSV
        df = pd.read_csv(csv_path)

        # Filter rows where Progress is empty
        unprocessed_rows = df[df['Progress'].isna()]

        if len(unprocessed_rows) == 0:
            logging.info("No new posts to process")
            return

        logging.info(f"Found {len(unprocessed_rows)} posts to process")

        # Process each row
        for index, row in tqdm(unprocessed_rows.iterrows(), total=len(unprocessed_rows)):
            try:
                filename = str(row['File Name'])
                title = str(row['Title'])
                content = str(row['Post Content'])

                # Combine title and content
                full_text = f"{title}. {content}"

                # Randomly select a voice preset
                random_voice = random.choice(npz_files)
                voice_preset = os.path.join(history_prompts_dir, random_voice)
                logging.info(f"Selected random voice: {voice_preset}")

                # Initialize TTS with the selected voice preset and temperature settings
                tts = TTSGenerator(voice_preset=voice_preset, text_temp=0.6, waveform_temp=0.8)

                # Generate output path
                output_path = os.path.join(output_dir, f"{filename}.wav")

                # Generate speech
                if tts.generate_speech(full_text, output_path):
                    df.at[index, 'Progress'] = 'TTS Generated'
                    df.to_csv(csv_path, index=False)
                    logging.info(f"Processed: {filename}")
                else:
                    logging.error(f"Failed to process: {filename}")

            except Exception as e:
                logging.error(f"Error processing row {index}: {str(e)}")
                traceback.print_exc()

    except Exception as e:
        logging.error(f"Error processing CSV: {str(e)}")
        traceback.print_exc()

def print_system_info():
    """
    Print system information for debugging
    """
    logging.info("\nSystem Information:")
    logging.info(f"Python Version: {sys.version}")
    try:
        logging.info(f"Torch Version: {torch.__version__}")
        logging.info(f"CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logging.info(f"CUDA Version: {torch.version.cuda}")
            logging.info(f"GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        logging.info("Torch not found.")
    try:
        import bark
        logging.info(f"Bark Version: {getattr(bark, '__version__', 'Unknown')}")
    except ImportError:
        logging.info("Bark not found.")

def main():
    """
    Main function to execute the script.
    """
    print_system_info()
    # Check if the CSV file path is provided as a command-line argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        logging.info(f"Using CSV file: {csv_path}")
        process_csv(csv_path=csv_path)
    else:
        logging.info("Using default CSV file: reddit_posts.csv")
        process_csv()  # Use the default path

if __name__ == "__main__":
    main()