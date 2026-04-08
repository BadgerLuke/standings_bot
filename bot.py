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

# New 2026 search tool configuration
search_tool = types.Tool(google_search=types.GoogleSearch())

# USE THE NEW 3.1 MODEL (Released April 2026)
# If 'gemini-3.1-flash' isn't in your region yet, use 'gemini-3-flash-preview'
CURRENT_MODEL = "gemini-3.1-flash"

# --- SPORTS POOL ---
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

    prompt = (
        f"Give me the current top 5 standings for {target}. "
        "Format: 'Rank. Team: Record (Pts/GB)'. "
        "1 line per team. No intro. Today is April 8, 2026."
    )
    
    # NEW: Safety settings to prevent "Empty Text" errors
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
        print(f"⚠️ Search failed: {e}. Trying fallback...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt + " (Use internal data)",
            config=types.GenerateContentConfig(safety_settings=safety_settings)
        )

    if response and response.text:
        try:
            standings_text = response.text.strip()
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            prefixes = ["Latest update:", "Current standings:", "State of play:", "Rankings update:"]
            prefix = random.choice(prefixes)
            league_tag = target.split(' ')[0]
            
            tweet_text = f"📊 {prefix} {target}\n\n{standings_text}\n\n🕒 {timestamp}\n#{league_tag} #SportsBot"
            
            # Post to X
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success! Posted to X.")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
    else:
        # Debugging: Why did it return nothing?
        if hasattr(response, 'candidates') and response.candidates:
            reason = response.candidates[0].finish_reason
            print(f"❌ API blocked response. Finish Reason: {reason}")
        else:
            print("❌ Absolute empty response from Google.")

if __name__ == "__main__":
    run()