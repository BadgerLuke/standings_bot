import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz

# --- API SETUP ---
# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize X (Twitter) Client
X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# Configuration for Google Search Grounding (April 2026 Syntax)
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
        f"Provide the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. No conversational intro."
    )
    
    try:
        # Use 'gemini-2.0-flash' - It's the stable workhorse until June 2026
        # It's less likely to trigger the "Limit: 0" error than the Preview models
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool]
            )
        )
        
        if not response.text:
            print("⚠️ No text returned. The Search Grounding might be blocked or safety-filtered.")
            return

        standings_text = response.text.strip()
        
        # Local Timestamp for Eden Prairie (Central Time)
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
        
        # Post to X
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Success! Posted {division} standings.")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        print("💡 TIP: If you see 'Limit: 0', you MUST link a billing account in AI Studio to verify your project.")

if __name__ == "__main__":
    run()