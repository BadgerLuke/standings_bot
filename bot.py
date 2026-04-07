import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz

# --- API SETUP ---
# Initialize the new 2026 Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Setup X (Twitter) Client
X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# Define the Google Search tool correctly for the new SDK
search_tool = types.Tool(google_search=types.GoogleSearch())

POOL = [
    "NHL Central Division", 
    "NHL Pacific Division", 
    "NHL Atlantic Division", 
    "NHL Metropolitan Division"
]

def run():
    division = random.choice(POOL)
    print(f"🤖 Grounding search for {division} standings...")

    prompt = (
        f"Give me the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. No intro or outro text."
    )
    
    try:
        # Generate grounded content
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool]
            )
        )
        
        if not response.text:
            print("⚠️ Gemini search returned no text. Check safety filters or API status.")
            return

        standings_text = response.text.strip()
        
        # Local Timestamp (Eden Prairie / Central Time)
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
        
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Successfully posted {division} at {timestamp}")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    run()