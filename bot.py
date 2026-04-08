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

search_tool = types.Tool(google_search=types.GoogleSearch())
# Using the stable 2026 workhorse model
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

    # We use a more "journalistic" prompt to avoid safety triggers
    prompt = (
        f"Act as a sports data journalist. Provide a neutral report of the top 5 standings for {target}. "
        "Format: 'Rank. Team: Record (Pts/GB)'. "
        "Provide only the list data. Today is April 8, 2026."
    )
    
    # NEW: Safety Overrides (Required for sports content in 2026)
    safety_settings = [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    ]

    response = None
    try:
        print(f"🔍 Fetching data with {CURRENT_MODEL}...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                safety_settings=safety_settings
            )
        )
    except Exception as e:
        print(f"⚠️ API Exception: {e}")
        return

    # Debugging the response structure
    if response and response.text:
        try:
            standings_text = response.text.strip()
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            league_tag = target.split(' ')[0]
            tweet_text = f"📊 {target} Standings\n\n{standings_text}\n\n🕒 {timestamp}\n#{league_tag} #SportsUpdates"
            
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success! Posted to X.")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
    else:
        # Check if it was blocked by safety
        if hasattr(response, 'candidates') and response.candidates:
            reason = response.candidates[0].finish_reason
            print(f"❌ Generation Blocked. Reason: {reason}")
        else:
            print("❌ Absolute empty response. This may be a temporary Google API outage.")

if __name__ == "__main__":
    run()