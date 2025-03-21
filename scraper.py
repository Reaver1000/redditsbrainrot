import praw
import os
import csv
from dotenv import load_dotenv
from prawcore.exceptions import ResponseException, NotFound
from replacements import sanitize_text  # Import sanitize_text from replacements.py

# Load environment variables
load_dotenv()

# Debug: Print environment variables
print(f"SUBREDDITS: {os.getenv('SUBREDDITS')}")
print(f"MIN_COMMENTS: {os.getenv('MIN_COMMENTS')}")
print(f"POST_LIMIT: {os.getenv('POST_LIMIT')}")
print(f"MIN_SCORE: {os.getenv('MIN_SCORE')}")
print(f"OUTPUT_FILE: {os.getenv('OUTPUT_FILE')}")

# Configuration
SUBREDDITS = os.getenv("SUBREDDITS", "AITAH+AmItheAsshole")
MIN_COMMENTS = int(os.getenv("MIN_COMMENTS", 5))
POST_LIMIT = int(os.getenv("POST_LIMIT", 10))
MIN_SCORE = int(os.getenv("MIN_SCORE", 100))
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reddit_posts.csv")

def get_reddit():
    """Initialize and return Reddit instance"""
    try:
        return praw.Reddit("bot1")  # Uses praw.ini config
    except ResponseException as e:
        print(f"❌ Reddit authentication failed: {e}")
        exit(1)

def get_existing_urls(file_path):
    """Fetch all existing URLs from the CSV file to avoid duplicates"""
    existing_urls = set()
    if os.path.isfile(file_path):
        try:
            with open(file_path, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) > 0:  # Ensure the row has a URL
                        existing_urls.add(row[0])  # URL is now in the first column
            print(f"📊 Found {len(existing_urls)} existing URLs in the CSV file.")
        except Exception as e:
            print(f"⚠️ Error reading existing URLs: {str(e)}")
            # Create a new file if there's an error with the existing one
            print(f"🔄 Creating a new CSV file: {file_path}")
    return existing_urls

def write_to_csv(data, file_path, existing_urls):
    """Write data to a local CSV file if not a duplicate, using UTF-8 encoding"""
    if data[0] in existing_urls:  # Check if URL already exists
        print(f"⏩ Skipping duplicate: {data[1][:60]}...")
        return False
    
    file_exists = os.path.isfile(file_path)
    print(f"📝 Writing to {'existing' if file_exists else 'new'} file: {file_path}")
    
    try:
        # Open the file in UTF-8 encoding and ensure newlines are handled correctly
        with open(file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                # Write header if the file doesn't exist
                writer.writerow(["URL", "Title", "Post Content"])
                print("📝 Added CSV header")
            writer.writerow(data)
            existing_urls.add(data[0])  # Add URL to the set to avoid future duplicates
        print(f"✅ Successfully wrote data to {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to write to CSV: {str(e)}")
        # Try creating the directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"📁 Created directory: {directory}")
                # Try writing again
                with open(file_path, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    if not file_exists:
                        writer.writerow(["URL", "Title", "Post Content"])
                    writer.writerow(data)
                print(f"✅ Successfully wrote data after creating directory")
                return True
            except Exception as e2:
                print(f"❌ Failed to create directory and write: {str(e2)}")
        return False

def process_submission(submission, existing_urls):
    """Process a submission and save to CSV if not a duplicate"""
    # Clean the post content using the sanitize_text function
    cleaned_content = sanitize_text(submission.selftext)
    
    submission_url = f"https://reddit.com{submission.permalink}"
    print(f"🔍 Processing submission: {submission_url}")

    row_data = [
        submission_url,  # URL is now first
        sanitize_text(submission.title),  # Sanitize the title as well
        cleaned_content,  # Use cleaned content
    ]

    try:
        success = write_to_csv(row_data, OUTPUT_FILE, existing_urls)
        if success:
            print(f"✅ Added: {submission.title[:60]}...")
        else:
            print(f"⚠️ Did not add: {submission.title[:60]}...")
    except Exception as e:
        print(f"❌ Failed to add {submission.id}: {str(e)}")

def scrape_posts():
    """Main scraping function"""
    reddit = get_reddit()
    existing_urls = get_existing_urls(OUTPUT_FILE)
    
    print(f"\n🔍 Scanning r/{SUBREDDITS} for quality posts...")
    subreddit = reddit.subreddit(SUBREDDITS)
    
    # Debug: Print subreddit details
    print(f"Subreddits being scanned: {subreddit.display_name}")
    
    posts_added = 0
    
    for submission in subreddit.hot(limit=POST_LIMIT):
        try:
            print(f"\nChecking post: {submission.title[:60]}...")
            print(f"Subreddit: {submission.subreddit.display_name}")
            print(f"Score: {submission.score}, Comments: {submission.num_comments}, NSFW: {submission.over_18}, Stickied: {submission.stickied}")
            
            if (submission.score >= MIN_SCORE 
                and not submission.over_18 
                and submission.num_comments >= MIN_COMMENTS
                and not submission.stickied):
                
                # Test if the submission content is valid
                if not submission.selftext.strip():
                    print("⏩ Skipping post (empty content)")
                    continue
                
                process_submission(submission, existing_urls)
                posts_added += 1
            else:
                reason = []
                if submission.score < MIN_SCORE:
                    reason.append(f"score too low ({submission.score} < {MIN_SCORE})")
                if submission.num_comments < MIN_COMMENTS:
                    reason.append(f"too few comments ({submission.num_comments} < {MIN_COMMENTS})")
                if submission.over_18:
                    reason.append("NSFW content")
                if submission.stickied:
                    reason.append("stickied post")
                
                print(f"⏩ Skipping post: {', '.join(reason)}")
                
        except NotFound:
            print(f"⚠️ Subreddit not found: {submission.subreddit.display_name}")
        except Exception as e:
            print(f"⚠️ Error processing {submission.id}: {str(e)}")
            continue
    
    print(f"\n📊 Added {posts_added} new posts to {OUTPUT_FILE}")

if __name__ == "__main__":
    print("🚀 Starting Reddit scraper")
    scrape_posts()
    print(f"🎉 Data saved to {OUTPUT_FILE}")