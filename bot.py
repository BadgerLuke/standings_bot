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
CURRENT_MODEL = "gemini-2.5-flash"

# Comprehensive 2026 Sports Pool
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

    # Strict formatting to stay under X's character limit
    prompt = (
        f"Give me current top 5 standings for {target}. "
        "Format: 'Rank. Team: Record (Pts/GB)'. "
        "Use 1 line per team. No conversational text. Be ultra-concise."
    )
    
    response = None
    try:
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
    except Exception as e:
        print(f"⚠️ Search tool skipped: {e}")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt + " (Use internal memory)."
        )

    if response and response.text:
        try:
            standings_text = response.text.strip()
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            # --- THE ANTI-403 LOGIC ---
            # 1. Add a random 'vibe' prefix to avoid duplicate content filters
            prefixes = ["Latest look at", "Updated standings for", "Current rankings:", "State of the", "Checking in on"]
            prefix = random.choice(prefixes)
            
            # 2. Dynamic Hashtags
            league_tag = target.split(' ')[0]
            
            # 3. Assemble Tweet
            tweet_text = f"📊 {prefix} {target}:\n\n{standings_text}\n\n🕒 {timestamp}\n#{league_tag} #Sports"
            
            # 4. Final Length Check (Safety for Free Tier)
            if len(tweet_text) > 275:
                tweet_text = tweet_text[:270] + "..."

            print(f"🐦 Posting:\n{tweet_text}")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success!")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
            print("💡 TIP: If this is a 403, try regenerating your X Access Tokens in the Dev Portal.")
    else:
        print("❌ Model failed to return text.")

if __name__ == "__main__":
    run()