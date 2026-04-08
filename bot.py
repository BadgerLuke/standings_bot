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
    
    # Anchor the AI to the actual current date
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz)
    current_date_str = now.strftime("%B %d, %2026")
    timestamp_str = now.strftime("%I:%M %p CT")
    
    print(f"🤖 Processing {target} for {current_date_str}...")

    season_term = "2026 season" if any(x in target for x in ["MLB", "MLS"]) else "2025-26 season"

    # Strict "Data Retrieval" prompt
    prompt = (
        f"Today is {current_date_str}. Use Google Search to find the ACTUAL standings "
        f"for the {target} {season_term}. List the top 5 teams. "
        "Format: Rank. Team: Record (Pts/GB). "
        "DO NOT give a disclaimer. DO NOT say you cannot predict the future. "
        "Simply output the factual data found in search results."
    )
    
    safety = [types.SafetySetting(category=c, threshold="BLOCK_NONE") for c in [
        "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
    ]]

    try:
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool], safety_settings=safety)
        )
        
        # Detection for the "As an AI..." refusal
        text = response.text or ""
        if "hypothetical" in text.lower() or "speculative" in text.lower() or "cannot provide" in text.lower():
            raise ValueError("Model gave a refusal disclaimer instead of data.")

    except Exception as e:
        print(f"⚠️ Search failed or refused: {e}. Trying raw fallback...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=f"List the top 5 standings for {target} as of {current_date_str}. Data only.",
            config=types.GenerateContentConfig(safety_settings=safety)
        )

    if response and response.text:
        # Scrub citations and refusals
        clean_text = re.sub(r'\[\d+\]', '', response.text.strip())
        
        # Final safety check: if the model STILL refused, don't post to X
        if "speculative" in clean_text.lower() or "predict" in clean_text.lower():
            print("❌ Post cancelled: Model persisted in refusal.")
            return

        league_tag = target.split(' ')[0]
        tweet_text = f"📊 {target} Standings\n({current_date_str})\n\n{clean_text}\n\n🕒 {timestamp_str}\n#{league_tag} #Sports"
        
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        try:
            print(f"🐦 Posting:\n{tweet_text}")
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print("🚀 SUCCESS!")
        except Exception as x_err:
            print(f"❌ X API Error: {x_err}")
    else:
        print("❌ No response content.")

if __name__ == "__main__":
    run()