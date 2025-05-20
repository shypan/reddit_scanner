import os
from datetime import datetime, timedelta
import praw
from dotenv import load_dotenv
import requests
import logging
load_dotenv()

# --- Configuration ---
REDDIT_CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SECRET = os.environ["REDDIT_SECRET"]
REDDIT_USER = os.environ["REDDIT_USER"]
REDDIT_PASS = os.environ["REDDIT_PASS"]
REDDIT_USER_AGENT = "KeywordScanner by /u/yourusername"
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SUBREDDITS = ["HungryArtists", "artcommissions", "commissions"]
KEYWORDS = ['[hiring]']
ALERT_WINDOW_MINUTES = 60

# --- Logging Setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "reddit_alert.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_SECRET,
                     user_agent=REDDIT_USER_AGENT,
                     username=REDDIT_USER,
                     password=REDDIT_PASS)

def scan_subreddits():
    now = datetime.now()
    alert_cutoff = now - timedelta(minutes=ALERT_WINDOW_MINUTES)
    matches = []

    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=50):
            if datetime.fromtimestamp(post.created_utc) < alert_cutoff:
                continue
            if any(keyword in post.title.lower() for keyword in KEYWORDS):
                matches.append(f"[{subreddit_name}] {post.title} — {post.shortlink}")
    return matches

def send_alert(matches):
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    message = "**Reddit Keyword Match(es):**\n" + "\n".join(matches)
    payload = {
        "content": message
    }

    response = requests.post(webhook_url, json=payload)
    if response.status_code != 204:
        print(f"Failed to send Discord alert: {response.status_code}, {response.text}")

def lambda_handler(event, context):
    load_dotenv()  # optional if using env vars set in Lambda instead
    matches = scan_subreddits()
    if matches:
        send_alert(matches)
    return {
        "statusCode": 200,
        "body": f"Sent {len(matches)} alert(s)" if matches else "No matches"
    }

matches = scan_subreddits()
print(matches)
if len(matches) > 0:
    send_alert(matches)
    for match in matches:
        logging.info(match)
else:
    logging.info("No matches")