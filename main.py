import subprocess
import os
import time
import sys

def run_script(script_name, description):
    """Run a Python script and check for success"""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Run the script
        result = subprocess.run([sys.executable, f"{script_name}.py"], check=True)

        # Calculate elapsed time
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)

        print(f"\n✅ {description} completed successfully!")
        print(f"⏱️ Time taken: {int(minutes)} minutes, {seconds:.2f} seconds")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ ERROR: Script '{script_name}.py' not found")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: An unexpected error occurred: {str(e)}")
        return False

def main():
    """Run the complete video generation pipeline"""
    print("\n" + "="*60)
    print("🚀 STARTING REDDIT VIDEO GENERATION PIPELINE")
    print("="*60)

    # Define the pipeline steps
    pipeline = [
        ("scraper", "Scraping Reddit content"),
        ("tts", "Converting text to speech"),
        ("subtitles", "Generating subtitles"),
        ("BGM", "Preparing background music"),
        ("video", "Creating final videos")
    ]

    # Track overall start time
    overall_start = time.time()

    # Run each step in sequence
    for script_name, description in pipeline:
        success = run_script(script_name, description)
        if not success:
            print("\n⛔ Pipeline stopped due to errors")
            return False

    # Calculate total time
    total_time = time.time() - overall_start
    minutes, seconds = divmod(total_time, 60)
    hours, minutes = divmod(minutes, 60)

    print("\n" + "="*60)
    print("✅ COMPLETE: All pipeline steps finished successfully!")
    print(f"⏱️ Total time: {int(hours)}h {int(minutes)}m {seconds:.2f}s")
    print("="*60)

    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")