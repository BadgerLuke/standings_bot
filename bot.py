import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz

# --- API SETUP ---
# The new SDK automatically picks up GEMINI_API_KEY from environment variables
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# Current Search Tool for 2026
search_tool = types.Tool(google_search=types.GoogleSearch())

# The official stable model for 2026
CURRENT_MODEL = "gemini-2.5-flash"

POOL = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference",
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West", "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def run():
    target = random.choice(POOL)
    print(f"🤖 Processing {target}...")

    prompt = (
        f"List the current top 5 standings for {target}. "
        "Format: 'Rank. Team: Record (Pts/GB)'. "
        "No intro. No conversational filler. Just the list."
    )
    
    response = None
    try:
        print(f"🔍 Fetching data with {CURRENT_MODEL}...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
    except Exception as e:
        print(f"⚠️ Search failed: {e}. Trying internal memory fallback...")
        try:
            response = client.models.generate_content(
                model=CURRENT_MODEL,
                contents=prompt + " (Use internal knowledge)."
            )
        except Exception as e2:
            print(f"❌ Both attempts failed: {e2}")
            return

    if response and response.text:
        try:
            standings_text = response.text.strip()
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            league_tag = target.split(' ')[0]
            tweet_text = f"📊 {target} Standings\n\n{standings_text}\n\n🕒 {timestamp}\n#{league_tag} #SportsUpdates"
            
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success! Posted {target} to X.")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
    else:
        print("❌ Model returned no text content.")

if __name__ == "__main__":
    run()