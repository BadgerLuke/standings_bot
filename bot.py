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

# Current 2026 search tool configuration
search_tool = types.Tool(google_search=types.GoogleSearch())

POOL = [
    "NHL Central Division", 
    "NHL Pacific Division", 
    "NHL Atlantic Division", 
    "NHL Metropolitan Division"
]

def run():
    division = random.choice(POOL)
    print(f"🤖 Processing {division}...")

    prompt = (
        f"Provide the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as: 'Rank. Team: W-L-OTL (Points)'. "
        "No intro text. Be concise."
    )
    
    try:
        # ATTEMPT 1: Search Grounded (Requires the 'Switch' to be on in AI Studio)
        print("🔍 Attempting grounded search...")
        response = client.models.generate_content(
            model="gemini-1.5-flash", # Use the stable LTS model
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
    except Exception as e:
        # ATTEMPT 2: Fallback (Internal Knowledge) if 403/429 occurs
        print(f"⚠️ Search failed ({e}). Falling back to internal memory...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt + " (Use your internal data if search is unavailable.)"
        )
    
    try:
        if response.text:
            standings_text = response.text.strip()
            
            # Timestamp (Eden Prairie / Central Time)
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
            
            X_CLIENT.create_tweet(text=tweet)
            print(f"🚀 Success! Posted {division}.")
        else:
            print("❌ No content generated.")

    except Exception as post_error:
        print(f"❌ Final error: {post_error}")

if __name__ == "__main__":
    run()