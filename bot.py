import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz
import re

# --- API SETUP ---
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# Use the base stable string
MODEL_ID = "gemini-2.0-flash"

ALL_DIVISIONS = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference",
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West", "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def get_active_pool(current_month):
    active = []
    for item in ALL_DIVISIONS:
        if "NFL" in item:
            if current_month in [9, 10, 11, 12, 1]: active.append(item)
        elif "MLB" in item:
            if 4 <= current_month <= 9: active.append(item)
        elif "NBA" in item or "NHL" in item:
            if current_month >= 10 or current_month <= 4: active.append(item)
        elif "MLS" in item:
            if 2 <= current_month <= 10: active.append(item)
    return active

def run():
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)
    date_label = now.strftime("%B %d, 2026")
    active_pool = get_active_pool(now.month)
    
    if not active_pool:
        print("⏸️ Offseason for all tracked leagues.")
        return

    target = random.choice(active_pool)
    print(f"🤖 Target: {target}")

    season = "2026" if any(x in target for x in ["MLB", "MLS"]) else "2025-26"
    prompt = (f"Current top 5 standings for {target} {season}. Today is {date_label}. "
              "Use Google Search. Format: Rank. Team: Record. No intro.")

    # List of models to try in order of preference
    # We use a loop so if one 404s, we move to the next without crashing
    potential_models = [MODEL_ID, "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    
    response = None
    for model_name in potential_models:
        try:
            print(f"🔍 Attempting {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
            )
            if response.text:
                print(f"✅ Success with {model_name}")
                break
        except Exception as e:
            print(f"⚠️ {model_name} failed: {e}")
            continue

    if response and response.text:
        # Clean response and format tweet
        clean_text = re.sub(r'\[\d+\]', '', response.text.strip())
        
        # Guard against AI lectures
        if any(x in clean_text.lower() for x in ["speculative", "cannot provide", "ai model"]):
            print("❌ Refusal detected.")
            return

        league_tag = target.split(' ')[0]
        tweet_text = f"📊 {target} Standings\n({date_label})\n\n{clean_text}\n\n🕒 {now.strftime('%I:%M %p CT')}\n#{league_tag} #Sports"
        
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        try:
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print("🚀 Posted successfully!")
        except Exception as x_err:
            print(f"❌ X Error: {x_err}")
    else:
        print("❌ All model attempts failed.")

if __name__ == "__main__":
    run()