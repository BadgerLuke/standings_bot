import os
import random
import tweepy
import google.generativeai as genai
from datetime import datetime
import pytz

# --- API SETUP ---
# Setup Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Setup X (Twitter)
X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# Initialize the Model with Google Search Grounding
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[{'google_search': {}}],
    system_instruction=(
        "You are a sports data assistant. When asked for standings, "
        "search for the most current 2025-26 data. Provide ONLY the "
        "top 5 teams in this exact plain-text format: 'Rank. Team: W-L-OTL (Points)'. "
        "Do not include any intro, outro, or conversational text."
    )
)

# The divisions we want to cycle through
POOL = [
    "NHL Central Division", 
    "NHL Pacific Division", 
    "NHL Atlantic Division", 
    "NHL Metropolitan Division"
]

def run():
    division = random.choice(POOL)
    print(f"🤖 Gemini is searching for {division} standings...")
    
    prompt = f"Give me the current top 5 standings for the {division}."
    
    try:
        # Generate content using Google Search
        response = model.generate_content(prompt)
        standings_text = response.text.strip()
        
        # Create a unique timestamp for Eden Prairie (Central Time)
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        # Construct the tweet
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL #Hockey"
        
        # Post to X
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Successfully posted to X at {timestamp}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    run()