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

# Tool for Google Search Grounding
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

    prompt = (
        f"Give me the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. No intro or outro text."
    )
    
    # We will try the newest Gemini 3 model first
    # If it fails, we fall back to the stable Gemini 2.5
    models_to_try = ["gemini-3-flash-preview", "gemini-2.5-flash"]
    
    for model_name in models_to_try:
        try:
            print(f"✨ Attempting with {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[search_tool]
                )
            )
            
            if response.text:
                standings_text = response.text.strip()
                
                # Timestamp for Eden Prairie (Central Time)
                tz = pytz.timezone('America/Chicago')
                timestamp = datetime.now(tz).strftime("%I:%M %p CT")
                
                tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
                
                X_CLIENT.create_tweet(text=tweet)
                print(f"🚀 Successfully posted {division} via {model_name}.")
                return # Exit once successful
            
        except Exception as e:
            print(f"⚠️ {model_name} failed: {e}")
            continue # Try the next model in the list

    print("❌ All models failed to generate content.")

if __name__ == "__main__":
    run()