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
# Alias for the latest stable model
CURRENT_MODEL = "gemini-2.0-flash-001" 

# Full list of all potential targets
ALL_DIVISIONS = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference",
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West", "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def get_active_pool(current_month):
    """Filters divisions based on whether the league is in regular season."""
    active = []
    for item in ALL_DIVISIONS:
        # NFL: Active Sept (9) thru Jan (1)
        if "NFL" in item:
            if current_month in [9, 10, 11, 12, 1]:
                active.append(item)
        # MLB: Active April (4) thru Sept (9)
        elif "MLB" in item:
            if 4 <= current_month <= 9:
                active.append(item)
        # NBA/NHL: Active Oct (10) thru April (4)
        elif "NBA" in item or "NHL" in item:
            if current_month >= 10 or current_month <= 4:
                active.append(item)
        # MLS: Active Feb (2) thru Oct (10)
        elif "MLS" in item:
            if 2 <= current_month <= 10:
                active.append(item)
    return active

def run():
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)
    current_month = now.month
    date_label = now.strftime("%B %d, 2026")
    
    # Get only active leagues for the current date
    active_pool = get_active_pool(current_month)
    
    if not active_pool:
        print("⏸️ No leagues are currently in regular season. Skipping post.")
        return

    target = random.choice(active_pool)
    print(f"🤖 Selected Active Target: {target}")

    season_term = "2026 season" if any(x in target for x in ["MLB", "MLS"]) else "2025-26 season"
    
    prompt = (
        f"Retrieve the current standings for the {target} {season_term}. "
        f"Today is {date_label}. Use Google Search. "
        "Format the top 5 teams as: Rank. Team: Record. "
        "Direct data only. No intro, no conversational filler."
    )

    try:
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
        
        text = response.text or ""
        # Check for AI 'Refusals'
        if any(x in text.lower() for x in ["speculative", "cannot provide", "not yet begun"]):
             raise ValueError("Model gave a refusal disclaimer.")

    except Exception:
        print("🔄 Primary search failed. Using blunt fallback...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=f"Top 5 {target} standings {season_term}. List only. No sentences."
        )

    if response and response.text:
        clean_text = re.sub(r'\[\d+\]', '', response.text.strip())
        
        # Final gate to keep the bot professional
        if "speculative" in clean_text.lower() or "ai" in clean_text.lower():
            print("❌ Failure: Model provided conversational text instead of data.")
            return

        league_tag = target.split(' ')[0]
        tweet_text = f"📊 {target} Standings\n({date_label})\n\n{clean_text}\n\n🕒 {now.strftime('%I:%M %p CT')}\n#{league_tag} #Sports"
        
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        try:
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 SUCCESS! Posted {target} standings.")
        except Exception as x_err:
            print(f"❌ X API Error: {x_err}")
    else:
        print("❌ Final response was empty.")

if __name__ == "__main__":
    run()