import os
from pathlib import Path

def get_input(prompt, default=None):
    """Helper function to get user input with a default value"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    value = input(prompt).strip()
    return value if value else default

def get_subreddits():
    """Get subreddits from user input"""
    print("\n📚 Subreddit Configuration")
    print("Recommended: AITAH+AmItheAsshole")
    print("Format: subreddit1+subreddit2+subreddit3")
    return get_input("Enter subreddits to scrape", "AITAH+AmItheAsshole")

def get_content_limits():
    """Get content length limits"""
    print("\n📏 Content Length Configuration")
    print("Recommended settings for TTS videos:")
    min_chars = get_input("Minimum characters (recommended: 500)", "500")
    optimal_chars = get_input("Optimal characters (recommended: 2000)", "2000")
    max_chars = get_input("Maximum characters (recommended: 3000)", "3000")
    return min_chars, optimal_chars, max_chars

def setup_reddit():
    """Configure Reddit API credentials"""
    print("\n🔑 Reddit API Setup")
    print("Get these from https://www.reddit.com/prefs/apps")
    client_id = get_input("Enter your Reddit Client ID")
    client_secret = get_input("Enter your Reddit Client Secret")
    user_agent = get_input("Enter your Reddit User Agent", "TTS Scraper (by u/YOUR_USERNAME)")
    
    # Save to praw.ini
    praw_config = f"""[bot1]
client_id = {client_id}
client_secret = {client_secret}
user_agent = {user_agent}
"""
    with open("praw.ini", "w") as f:
        f.write(praw_config)
    print("✅ Reddit credentials saved to praw.ini")

def setup_env_file():
    """Configure all environment variables"""
    print("\n⚙️ Configuration Setup")
    
    # Get user inputs
    subreddits = get_subreddits()
    min_chars, optimal_chars, max_chars = get_content_limits()
    posts_per_sub = get_input("Number of posts per subreddit", "10")
    
    # Create comprehensive .env file
    env_config = f"""# Reddit Configuration
SUBREDDITS={subreddits}
MIN_COMMENTS=5
POST_LIMIT=100
MIN_SCORE=100
OUTPUT_FILE=reddit_posts.csv

# Content Length Settings
MIN_CHARS={min_chars}
OPTIMAL_CHARS={optimal_chars}
MAX_CHARS={max_chars}
MIN_TITLE_CHARS=30
MAX_TITLE_CHARS=200

# Processing Settings
POSTS_PER_SUBREDDIT={posts_per_sub}
"""
    with open(".env", "w") as f:
        f.write(env_config)
    print("✅ Configuration saved to .env")

def create_directories():
    """Create necessary directories"""
    directories = [
        "BackgroundVideos",
        "FinalVideos",
        "Subtitles",
        "Voiceovers"
    ]
    
    print("\n📁 Creating directories...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/")

def setup_project():
    """Main setup function"""
    print("🚀 Reddit Scraper Setup")
    
    # Create directories first
    create_directories()
    
    # Setup configurations
    setup_reddit()
    setup_env_file()
    
    print("\n🎉 Setup complete! Your environment is ready.")
    print("\nNext steps:")
    print("1. Add background videos to BackgroundVideos/")
    print("2. Run the scraper to collect stories")
    print("3. Add voiceovers to Voiceovers/")
    print("4. Generate final videos")

if __name__ == "__main__":
    setup_project()