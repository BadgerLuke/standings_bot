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

# New 2026 Primary Alias
PREFERRED_MODEL = "gemini-3-flash-preview"

ALL_DIVISIONS = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference"
]

def run():
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)
    date_label = now.strftime("%B %d, 2026")
    
    target = random.choice(ALL_DIVISIONS)
    print(f"🤖 Target: {target}")

    season = "2026" if any(x in target for x in ["MLB", "MLS"]) else "2025-26"
    prompt = f"Current top 5 standings for {target} {season}. Today is {date_label}. Use Google Search. Format: Rank. Team: Record. No intro."

    # --- AUTO-DISCOVERY LOGIC ---
    working_model = None
    try:
        # Check if our preferred model works
        client.models.get(model=PREFERRED_MODEL)
        working_model = PREFERRED_MODEL
    except:
        print(f"⚠️ {PREFERRED_MODEL} not found. Searching for active models...")
        try:
            # Dynamically fetch whatever Flash model Google is currently serving
            available = [m.name for m in client.models.list() if "flash" in m.name.lower()]
            if available:
                working_model = available[0].replace("models/", "") 
                print(f"✅ Found working alternative: {working_model}")
        except Exception as e:
            print(f"❌ Could not list models: {e}")
            return

    if not working_model:
        print("❌ No compatible models found for this API key.")
        return

    try:
        response = client.models.generate_content(
            model=working_model,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        )
        
        if response and response.text:
            clean_text = re.sub(r'\[\d+\]', '', response.text.strip())
            
            # Post to X
            league_tag = target.split(' ')[0]
            tweet_text = f"📊 {target} Standings\n({date_label})\n\n{clean_text}\n\n🕒 {now.strftime('%I:%M %p CT')}\n#{league_tag} #Sports"
            
            X_CLIENT.create_tweet(text=tweet_text[:280], user_auth=True)
            print(f"🚀 SUCCESS! Posted using {working_model}")
        else:
            print("❌ Model returned no content.")
            
    except Exception as e:
        print(f"❌ Execution error: {e}")

if __name__ == "__main__":
    run()