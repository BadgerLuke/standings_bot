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

# Ensure these match your REGENERATED tokens after setting App to Read/Write
X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

search_tool = types.Tool(google_search=types.GoogleSearch())
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

    # Dynamic season logic
    season_term = "current 2026 season" if any(x in target for x in ["MLB", "MLS"]) else "2025-26 season"

    prompt = (
        f"Official top 5 standings for {target} {season_term}. "
        "Format: Rank. Team: Record. "
        "Strictly data only. No intro, no warnings, no future speculation."
    )
    
    # Standard safety for sports
    safety = [types.SafetySetting(category=c, threshold="BLOCK_NONE") for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]

    try:
        print(f"🔍 Fetching {target}...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool], safety_settings=safety)
        )
        
        # Check if the AI lectured us or failed
        text = response.text or ""
        if "speculative" in text.lower() or "cannot provide" in text.lower() or len(text) < 10:
             raise ValueError("Bad response content")

    except:
        print("⚠️ Search failed/refused. Using internal fallback...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=f"Top 5 {target} teams and records as of April 2026. No intro.",
            config=types.GenerateContentConfig(safety_settings=safety)
        )

    if response and response.text:
        # 1. Clean citations
        clean_text = re.sub(r'\[\d+\]', '', response.text.strip())
        
        # 2. Build Tweet
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        league_tag = target.split(' ')[0]
        tweet_text = f"📊 {target}:\n\n{clean_text}\n\n🕒 {timestamp}\n#{league_tag} #Standings"
        
        # 3. Final Length Safety (X limit is 280)
        if len(tweet_text) > 270:
            tweet_text = tweet_text[:267] + "..."

        try:
            print(f"🐦 Posting:\n{tweet_text}")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print("🚀 SUCCESS!")
        except Exception as x_err:
            print(f"❌ X API Error: {x_err}")
            print("💡 TIP: Check if your X App is set to 'Read and Write' in the Dev Portal.")
    else:
        print("❌ No text generated.")

if __name__ == "__main__":
    run()