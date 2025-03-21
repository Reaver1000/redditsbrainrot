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

def setup_reddit():
    """Configure Reddit API credentials"""
    print("\n🔑 Reddit API Setup")
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

def setup_local_csv():
    """Configure local CSV file settings"""
    print("\n📄 Local CSV Setup")
    output_file = get_input("Enter the path for the output CSV file", "reddit_posts.csv")
    
    # Save to .env
    env_config = f"""# Reddit Configuration
SUBREDDITS=hfy+meta_reddit+AmItheAsshole
MIN_COMMENTS=5
POST_LIMIT=15
MIN_SCORE=100

# Local CSV Configuration
OUTPUT_FILE={output_file}
"""
    with open(".env", "w") as f:
        f.write(env_config)
    print("✅ Local CSV configuration saved to .env")

def setup_project():
    """Main setup function"""
    print("🚀 Reddit Scraper Setup")
    setup_reddit()
    setup_local_csv()
    print("\n🎉 Setup complete! You can now run the scraper.")

if __name__ == "__main__":
    setup_project()