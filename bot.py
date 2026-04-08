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
CURRENT_MODEL = "gemini-2.0-flash" # Reverting to the most stable 2026 ID

POOL = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference",
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West", "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def run():
    target = random.choice(POOL)
    
    # Clean Date Logic
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)
    date_label = now.strftime("%B %d, 2026")
    timestamp_label = now.strftime("%I:%M %p CT")
    
    print(f"🤖 Processing {target} for {date_label}...")

    season_term = "2026 season" if any(x in target for x in ["MLB", "MLS"]) else "2025-26 season"

    # Stage 1: Attempt Grounded Search
    prompt = (
        f"Provide the current top 5 standings for the {target} {season_term}. "
        f"Today is {date_label}. Use Google Search. "
        "Format: Rank. Team: Record (Pts/GB). List only. No intro text."
    )
    
    response_text = None
    
    try:
        print("🔍 Attempting Grounded Search...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
        if response.text and "Rank." in response.text:
            response_text = response.text
    except Exception as e:
        print(f"⚠️ Search failed: {e}")

    # Stage 2: Fallback to Internal Knowledge if Stage 1 failed
    if not response_text:
        print("🔄 Falling back to internal knowledge...")
        try:
            fallback_prompt = f"List the top 5 teams in the {target} as of early April 2026. Format: Team (Record). No intro."
            response = client.models.generate_content(
                model=CURRENT_MODEL,
                contents=fallback_prompt
            )
            response_text = response.text
        except Exception as e2:
            print(f"❌ Critical Error: Fallback also failed: {e2}")
            return

    # Post Processing & Tweeting
    if response_text:
        # Clean up citation markers like [1], [2]
        clean_standings = re.sub(r'\[\d+\]', '', response_text.strip())
        
        # Guard against the "As an AI..." lecture
        if "speculative" in clean_standings.lower() or "cannot predict" in clean_standings.lower():
            print("❌ Refusal detected in response. Aborting post.")
            return

        league_tag = target.split(' ')[0]
        tweet_text = f"📊 {target} Standings\n({date_label})\n\n{clean_standings}\n\n🕒 {timestamp_label}\n#{league_tag} #Sports"
        
        # X character limit safety
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        try:
            print(f"🐦 Posting to X...")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print("🚀 SUCCESS!")
        except Exception as x_err:
            print(f"❌ X API Error: {x_err}")
    else:
        print("❌ Final response was empty.")

if __name__ == "__main__":
    run()