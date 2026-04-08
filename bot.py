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
        f"Search for the current top 5 standings of the {target} for the 2025-26 season. "
        "Return ONLY a list in this format: 'Rank. Team: Record (Pts/GB)'. "
        "Do not include any other text, analysis, or citations."
    )
    
    safety_settings = [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    ]

    response = None
    try:
        print(f"🔍 Attempt 1: Grounded Search...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                safety_settings=safety_settings
            )
        )
        
        # If Attempt 1 returned nothing, trigger the fallback immediately
        if not response.text:
            raise ValueError("Empty response text")
            
    except Exception as e:
        print(f"⚠️ Attempt 1 failed or empty ({e}). Switching to Fallback...")
        response = client.models.generate_content(
            model=CURRENT_MODEL,
            contents=f"Provide the 2025-26 standings for {target}. Format as a list. No intro.",
            config=types.GenerateContentConfig(safety_settings=safety_settings)
        )

    if response and response.text:
        try:
            standings_text = response.text.strip()
            
            # If the model still gave us citations [1], [2], clean them out for X
            import re
            standings_text = re.sub(r'\[\d+\]', '', standings_text)
            
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
        print("❌ Critical: Both attempts returned no content.")

if __name__ == "__main__":
    run()