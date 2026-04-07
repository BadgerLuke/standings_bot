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

# Search Tool Configuration (Required for Live Standings)
search_tool = types.Tool(google_search=types.GoogleSearch())

POOL = [
    "NHL Central Division", 
    "NHL Pacific Division", 
    "NHL Atlantic Division", 
    "NHL Metropolitan Division"
]

def run():
    division = random.choice(POOL)
    print(f"🤖 Searching Google for {division} standings...")

    # Force Gemini to be concise to fit within X.com character limits
    prompt = (
        f"Provide the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. "
        "Do not include any intro, outro, or conversational text."
    )
    
    try:
        # Using the current 2026 standard model
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool]
            )
        )
        
        if not response.text:
            print("⚠️ Response was empty. Check if billing/verification is required for Search.")
            return

        standings_text = response.text.strip()
        
        # Local Timestamp (Central Time)
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        # Build Tweet
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL #HockeyBot"
        
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Successfully posted {division} at {timestamp}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if "RESOURCE_EXHAUSTED" in str(e):
            print("💡 ACTION REQUIRED: You must link a Billing Account in AI Studio to use Google Search.")

if __name__ == "__main__":
    run()