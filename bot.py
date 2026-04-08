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

search_tool = types.Tool(google_search=types.GoogleSearch())

# This is the current "Latest" stable alias for April 2026
LATEST_MODEL = "gemini-2.0-flash-001" 

POOL = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference",
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West", "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def run():
    target = random.choice(POOL)
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)
    date_label = now.strftime("%B %d, 2026")
    timestamp_label = now.strftime("%I:%M %p CT")
    
    print(f"🤖 Processing {target} for {date_label}...")

    season_term = "2026 season" if any(x in target for x in ["MLB", "MLS"]) else "2025-26 season"
    prompt = (
        f"Provide the current top 5 standings for the {target} {season_term}. "
        f"Today is {date_label}. Use Google Search. "
        "Format: Rank. Team: Record (Pts/GB). List only. No intro text."
    )

    # --- AUTO-HEALING MODEL SELECTION ---
    # We try our preferred model, but if it fails, we ask the API what IS available.
    try:
        model_to_use = LATEST_MODEL
        print(f"🔍 Attempting Search with {model_to_use}...")
        response = client.models.generate_content(
            model=model_to_use,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
    except Exception as e:
        print(f"⚠️ {model_to_use} failed. Searching for an alternative model...")
        try:
            # Dynamically find ANY flash model available to your key
            available_models = [m.name for m in client.models.list() if "flash" in m.name]
            model_to_use = available_models[0] if available_models else "gemini-1.5-flash"
            print(f"🔄 Switching to {model_to_use}...")
            response = client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=types.GenerateContentConfig(tools=[search_tool])
            )
        except Exception as e2:
            print(f"❌ Critical Error: No models available. {e2}")
            return

    # --- POSTING LOGIC ---
    if response and response.text:
        clean_standings = re.sub(r'\[\d+\]', '', response.text.strip())
        
        # Guard against AI "Refusal" lectures
        if "speculative" in clean_standings.lower() or "cannot predict" in clean_standings.lower():
            print("❌ Refusal detected. Bot won't post garbage.")
            return

        league_tag = target.split(' ')[0]
        tweet_text = f"📊 {target} Standings\n({date_label})\n\n{clean_standings}\n\n🕒 {timestamp_label}\n#{league_tag} #Sports"
        
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        try:
            print(f"🐦 Posting to X...")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print("🚀 SUCCESS!")
        except Exception as x_err:
            print(f"❌ X API Error: {x_err}")
    else:
        print("❌ Model returned no text.")

if __name__ == "__main__":
    run()