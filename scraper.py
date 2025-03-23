import praw
import os
import csv
from dotenv import load_dotenv
from prawcore.exceptions import ResponseException, NotFound
from replacements import sanitize_text
import sqlite3
from datetime import datetime, timedelta
import hashlib

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

def generate_story_id(title, content):
    """Generate unique ID for story"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    content_hash = hashlib.md5(f"{title}{content}".encode()).hexdigest()[:4]
    return f"STORY_{timestamp}_{content_hash}"

class URLTracker:
    def __init__(self):
        self.db_path = 'url_tracker.db'
        self.retention_days = 90  # 3 months retention
        self.setup_db()
        self.cleanup_old_urls()

    def setup_db(self):
        """Create SQLite database for URL tracking only"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS urls
                    (url TEXT PRIMARY KEY,
                     scraped_date TEXT)''')
        conn.commit()
        conn.close()

    def is_duplicate(self, url):
        """Check if URL has been seen in the last 3 months"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        three_months_ago = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        c.execute('SELECT url FROM urls WHERE url = ? AND scraped_date > ?', 
                 (url, three_months_ago))
        result = c.fetchone() is not None
        conn.close()
        return result

    def cleanup_old_urls(self):
        """Remove URLs older than 3 months"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        three_months_ago = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        c.execute('DELETE FROM urls WHERE scraped_date < ?', (three_months_ago,))
        conn.commit()
        conn.close()

    def add_url(self, url):
        """Add URL to tracking database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO urls VALUES (?, ?)', 
                     (url, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()

class AdaptiveThresholds:
    def __init__(self):
        self.db_path = 'thresholds.db'
        self.target_posts = int(os.getenv("POSTS_PER_SUBREDDIT", 10))
        self.adjustment_rate = 0.1  # How quickly to adjust thresholds
        self.setup_db()

    def setup_db(self):
        """Setup database to store and track thresholds"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS thresholds
                    (metric TEXT PRIMARY KEY,
                     current_value FLOAT,
                     success_rate FLOAT,
                     last_adjusted TEXT)''')
        
        # Initialize default thresholds if not exists
        default_thresholds = {
            'score_weight': 0.3,
            'velocity_weight': 0.2,
            'comment_ratio_weight': 0.2,
            'awards_weight': 0.1,
            'length_weight': 0.2,
            'min_score_multiplier': 1.0,
            'min_comments_multiplier': 1.0
        }
        
        for metric, value in default_thresholds.items():
            c.execute('''INSERT OR IGNORE INTO thresholds 
                        (metric, current_value, success_rate, last_adjusted)
                        VALUES (?, ?, 0, CURRENT_TIMESTAMP)''', 
                     (metric, value))
        
        conn.commit()
        conn.close()

    def get_current_thresholds(self):
        """Get current threshold values"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT metric, current_value FROM thresholds')
        thresholds = dict(c.fetchall())
        conn.close()
        return thresholds

    def adjust_thresholds(self, posts_found):
        """Adjust thresholds based on results"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Calculate how far off we are from target
        ratio = posts_found / self.target_posts
        should_increase = ratio > 1.2  # Too many posts
        should_decrease = ratio < 0.8  # Too few posts
        
        if should_increase or should_decrease:
            adjustment = self.adjustment_rate * (1 if should_increase else -1)
            thresholds = self.get_current_thresholds()
            
            # Adjust each threshold
            for metric, current_value in thresholds.items():
                new_value = current_value * (1 + adjustment)
                
                # Ensure weights stay reasonable
                if 'weight' in metric:
                    new_value = max(0.1, min(0.5, new_value))
                else:
                    new_value = max(0.5, new_value)  # For multipliers
                
                c.execute('''UPDATE thresholds 
                           SET current_value = ?,
                               last_adjusted = CURRENT_TIMESTAMP
                           WHERE metric = ?''', 
                         (new_value, metric))
                
                print(f"Adjusted {metric}: {current_value:.2f} -> {new_value:.2f}")
        
        conn.commit()
        conn.close()

class ContentLengthFilter:
    def __init__(self):
        self.min_chars = int(os.getenv("MIN_CHARS", 500))
        self.optimal_chars = int(os.getenv("OPTIMAL_CHARS", 2000))
        self.max_chars = int(os.getenv("MAX_CHARS", 3000))
        self.min_title_chars = int(os.getenv("MIN_TITLE_CHARS", 30))
        self.max_title_chars = int(os.getenv("MAX_TITLE_CHARS", 200))

    def check_length(self, title: str, content: str) -> tuple[bool, str, float]:
        title_length = len(title)
        content_length = len(content)
        
        if title_length < self.min_title_chars:
            return False, "Title too short", 0.0
        if title_length > self.max_title_chars:
            return False, "Title too long", 0.0
            
        if content_length < self.min_chars:
            return False, f"Content too short ({content_length} chars)", 0.0
        if content_length > self.max_chars:
            return False, f"Content too long ({content_length} chars)", 0.0
            
        if content_length <= self.optimal_chars:
            length_score = content_length / self.optimal_chars
        else:
            overage = (content_length - self.optimal_chars) / (self.max_chars - self.optimal_chars)
            length_score = 1.0 - overage
            
        return True, "Length OK", length_score

class PostRanker:
    def __init__(self):
        self.target_posts = int(os.getenv("POSTS_PER_SUBREDDIT", 10))
        self.length_filter = ContentLengthFilter()
        self.adaptive_thresholds = AdaptiveThresholds()
        self.thresholds = self.adaptive_thresholds.get_current_thresholds()

    def rank_post(self, submission):
        try:
            passes_length, length_reason, length_score = self.length_filter.check_length(
                submission.title,
                submission.selftext
            )
            
            if not passes_length:
                return 0.0, length_reason

            # Get current thresholds
            weights = self.thresholds
            
            # Calculate metrics with adaptive weights
            age_hours = (datetime.utcnow() - datetime.fromtimestamp(submission.created_utc)).total_seconds() / 3600
            velocity = submission.score / max(1, age_hours)
            comment_ratio = submission.num_comments / (submission.score + 1)
            awards = getattr(submission, 'total_awards_received', 0)

            score_norm = min(1.0, submission.score / 1000)
            velocity_norm = min(1.0, velocity / 100)
            comment_ratio_norm = min(1.0, comment_ratio / 0.5)
            awards_norm = min(1.0, awards / 5)

            # Use adaptive weights
            total_score = (
                score_norm * weights['score_weight'] +
                velocity_norm * weights['velocity_weight'] +
                comment_ratio_norm * weights['comment_ratio_weight'] +
                awards_norm * weights['awards_weight'] +
                length_score * weights['length_weight']
            )

            if any(phrase in submission.title.lower() for phrase in 
                  ['aita', 'am i the', 'wibta', 'would i be']):
                total_score *= 1.2

            return total_score, "OK"

        except Exception as e:
            return 0.0, f"Error: {str(e)}"

def get_reddit():
    """Initialize and return Reddit instance"""
    try:
        return praw.Reddit("bot1")  # Uses praw.ini config
    except ResponseException as e:
        print(f"❌ Reddit authentication failed: {e}")
        exit(1)

def write_to_csv(data, file_path, url_tracker):
    """Write data to CSV maintaining title and content in columns B and C"""
    submission_url = data[0]
    virality_score = int(data[3] * 100)
    story_id = generate_story_id(data[1], data[2])
    
    # Check for duplicate
    if url_tracker.is_duplicate(submission_url):
        print(f"⏩ Skipping duplicate: {data[1][:60]}...")
        return False
    
    file_exists = os.path.isfile(file_path)
    
    try:
        with open(file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "Story_ID",     # Column A: Story ID
                    "Title",        # Column B: Title (maintained position)
                    "Content",      # Column C: Content (maintained position)
                    "Score"         # Column D: Score
                ])
            
            writer.writerow([
                story_id,          # Column A: Story ID
                data[1],           # Column B: Title
                data[2],           # Column C: Content
                virality_score     # Column D: Score
            ])
            
            url_tracker.add_url(submission_url)
            print(f"✅ Added post with ID: {story_id} (score: {virality_score})")
            return True
            
    except Exception as e:
        print(f"❌ Failed to write to CSV: {str(e)}")
        return False
def process_submission(submission, url_tracker, virality_score):
    """Process a submission and save to CSV if not a duplicate"""
    submission_url = f"https://reddit.com{submission.permalink}"
    
    row_data = [
        submission_url,
        sanitize_text(submission.title),
        sanitize_text(submission.selftext),
        virality_score
    ]

    try:
        success = write_to_csv(row_data, OUTPUT_FILE, url_tracker)
        if success:
            print(f"✅ Added (score: {int(virality_score * 100)}): {submission.title[:60]}...")
        else:
            print(f"⚠️ Did not add: {submission.title[:60]}...")
    except Exception as e:
        print(f"❌ Failed to add {submission.id}: {str(e)}")

def scrape_posts():
    """Main scraping function with ranking"""
    reddit = get_reddit()
    url_tracker = URLTracker()
    ranker = PostRanker()
    
    subreddit_list = SUBREDDITS.split('+')
    posts_per_subreddit = int(os.getenv("POSTS_PER_SUBREDDIT", 10))
    
    print(f"\n🔍 Scanning for {posts_per_subreddit} posts per subreddit")
    print(f"Content length limits: {ranker.length_filter.min_chars}-{ranker.length_filter.max_chars} chars")
    
    all_processed_posts = []
    
    for subreddit_name in subreddit_list:
        print(f"\n📍 Scanning r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)
        ranked_posts = []
        
        for submission in subreddit.hot(limit=POST_LIMIT):
            try:
                if url_tracker.is_duplicate(f"https://reddit.com{submission.permalink}"):
                    continue

                if (submission.score >= MIN_SCORE 
                    and not submission.over_18 
                    and submission.num_comments >= MIN_COMMENTS
                    and not submission.stickied
                    and submission.selftext.strip()):

                    rank, reason = ranker.rank_post(submission)
                    
                    if rank > 0:
                        ranked_posts.append((submission, rank))
                        print(f"✅ Potential post (rank: {rank:.2f}): {submission.title[:60]}...")
                    else:
                        print(f"❌ Skipped post: {reason}")

            except Exception as e:
                print(f"⚠️ Error: {str(e)}")
                continue

        # Sort and take top N
        ranked_posts.sort(key=lambda x: x[1], reverse=True)
        top_posts = ranked_posts[:posts_per_subreddit]
        
        if top_posts:
            print(f"\n🏆 Top {len(top_posts)} posts from r/{subreddit_name}:")
            for submission, rank in top_posts:
                content_length = len(submission.selftext)
                print(f"\nRank: {rank:.2f}, Length: {content_length} chars")
                print(f"Title: {submission.title}")
                all_processed_posts.append((submission, rank, subreddit_name))
        else:
            print(f"\n❌ No suitable posts found in r/{subreddit_name}")

    # Process all top posts
    print("\n✍️ Processing final selection...")
    for submission, rank, subreddit_name in all_processed_posts:
        process_submission(submission, url_tracker, rank)
        print(f"✅ Added post from r/{subreddit_name} (rank: {rank:.2f})")

    # Adjust thresholds based on results
    ranker.adaptive_thresholds.adjust_thresholds(len(all_processed_posts))
    
    print(f"\n📊 Total posts processed: {len(all_processed_posts)}")
    print("\n🔄 Thresholds adjusted for next run")

if __name__ == "__main__":
    print("🚀 Starting Reddit scraper")
    scrape_posts()
    print(f"🎉 Data saved to {OUTPUT_FILE}")