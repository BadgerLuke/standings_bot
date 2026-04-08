import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime
import pytz
import re

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

    # Determine the correct season terminology for the specific sport
    if "MLB" in target or "MLS" in target:
        season_term = "current 2026 season"
    else:
        season_term = "current 2025-26 season"

    # Use a prompt that demands factual data to bypass "future speculation" guardrails
    prompt = (
        f"Retrieve the official standings for the {target} for the {season_term}. "
        "List only the top 5 teams. Format: 'Rank. Team: Record (Pts/GB)'. "
        "Do not include any commentary about unpredictability or speculative outcomes."
    )
    
    safety_settings = [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    ]

    response = None
    try:
        print(f"🔍 Grounded Search for {season_term}...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                safety_settings=safety_settings
            )
        )
        # Force a failure if the AI gives a refusal message instead of a list
        if not response.text or "speculative" in response.text.lower() or "cannot provide" in response.text.lower():
            raise ValueError("Model refused to provide data or returned empty.")
            
    except Exception as e:
        print(f"⚠️ Attempt 1 failed: {e}. Trying Fallback...")
        # Fallback uses a more direct command
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=f"Standing list for {target} {season_term}. Format: Team (Record). No intro.",
            config=types.GenerateContentConfig(safety_settings=safety_settings)
        )

    if response and response.text:
        try:
            standings_text = re.sub(r'\[\d+\]', '', response.text.strip())
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            league_tag = target.split(' ')[0]
            tweet_text = f"📊 {target} Standings\n\n{standings_text}\n\n🕒 {timestamp}\n#{league_tag} #Sports"
            
            print(f"🐦 Posting to X...")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success!")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
    else:
        print("❌ Critical: Failed to get data.")

if __name__ == "__main__":
    run()