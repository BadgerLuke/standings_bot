import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz

# --- API SETUP ---
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

search_tool = types.Tool(google_search=types.GoogleSearch())
CURRENT_MODEL = "gemini-2.5-flash"

# --- EXPANDED SPORTS POOL ---
POOL = [
    # NHL
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    # NBA
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", 
    "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    # MLB
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    # MLS
    "MLS Eastern Conference", "MLS Western Conference",
    # NFL (Final 2025-26 Standings)
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West",
    "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def run():
    target = random.choice(POOL)
    print(f"🤖 Processing {target}...")

    # Dynamic prompt that adjusts for the specific league/current date
    prompt = (
        f"Provide the current top 5 standings for {target}. "
        "If the season is over (like NFL), provide the final regular season standings for 2025-26. "
        "Format exactly as a list: 'Rank. Team: Record (Points/GB if applicable)'. "
        "No intro text, no conversational filler. Just the list."
    )
    
    response = None
    
    # --- GEMINI SECTION ---
    try:
        print(f"🔍 Fetching live data for {target}...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
    except Exception as e:
        print(f"⚠️ Search tool skipped: {e}")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt + " (Use internal memory)."
        )

    # --- TWITTER SECTION ---
    if response and response.text:
        try:
            standings_text = response.text.strip()
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            # Extract league name for the hashtag
            league_tag = target.split(' ')[0]
            tweet_text = f"📊 {target} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#{league_tag} #SportsBot"
            
            print(f"🐦 Posting to X...")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success!")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
    else:
        print("❌ Model failed to return text.")

if __name__ == "__main__":
    run()