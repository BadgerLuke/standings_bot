import os
import random
import tweepy
import google.generativeai as genai
from google import genai
from google.genai import types
from datetime import datetime
import pytz

# --- API SETUP ---
# Setup Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
# Setup New Gemini SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Setup X (Twitter)
X_CLIENT = tweepy.Client(
@@ -17,19 +18,10 @@
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
# Configuration for Google Search Grounding
# Note: In the new SDK, tools are passed in the config
search_tool = types.Tool(google_search=types.GoogleSearch())

# The divisions we want to cycle through
POOL = [
    "NHL Central Division", 
    "NHL Pacific Division", 
@@ -39,28 +31,36 @@

# --- UPDATE THIS SECTION IN bot.py ---

def run():
    division = random.choice(POOL)
    print(f"🤖 Searching Google for {division}...")

    prompt = (
        f"Give me the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. No intro text."
    )
    
    try:
        # CHANGED: model="gemini-1.5-flash" (The stable free-tier workhorse)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool]
            )
        )
        
        # Check if the response actually has text (sometimes safety filters block sports data)
        if not response.text:
            print("⚠️ Gemini returned an empty response. Likely a safety filter trigger.")
            return

        standings_text = response.text.strip()
        
        # Timestamp logic...
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
        
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Posted {division} successfully.")
        
    except Exception as e:
        # If it still says 429, it means your "Search" tool is blocked on the anonymous tier
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()