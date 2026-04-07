import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz

# --- API SETUP ---
# Setup New Gemini SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Setup X (Twitter)
X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# Configuration for Google Search Grounding
# Note: In the new SDK, tools are passed in the config
search_tool = types.Tool(google_search=types.GoogleSearch())

POOL = [
    "NHL Central Division", 
    "NHL Pacific Division", 
    "NHL Atlantic Division", 
    "NHL Metropolitan Division"
]

def run():
    division = random.choice(POOL)
    print(f"🤖 Searching Google for {division}...")

    prompt = (
        f"Give me the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. No intro text."
    )
    
    try:
        # The new 2026 way to generate grounded content
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Using the latest stable 2026 model
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool]
            )
        )
        
        standings_text = response.text.strip()
        
        # Timestamp for Eden Prairie (Central Time)
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
        
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Posted {division} successfully.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()