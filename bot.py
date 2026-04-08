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

POOL = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference",
    "NFL AFC East", "NFL AFC North", "NFL AFC South", "NFL AFC West", "NFL NFC East", "NFL NFC North", "NFL NFC South", "NFL NFC West"
]

def get_best_flash_model():
    """Dynamically fetches the highest available flash model for your API key."""
    available_models = []
    try:
        # Ask the API what models this specific key is allowed to use
        for m in client.models.list():
            if "flash" in m.name and "generateContent" in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        print(f"⚠️ Could not list models: {e}")
        return "gemini-1.5-flash" # The ultimate real-world fallback
    
    if not available_models:
         return "gemini-1.5-flash"
         
    # Sort the list so the highest version number is first (e.g., 2.0 before 1.5)
    available_models.sort(reverse=True)
    return available_models[0]

def run():
    target = random.choice(POOL)
    print(f"🤖 Processing {target}...")

    # Step 1: Dynamically find the right model
    active_model = get_best_flash_model()
    print(f"✅ Selected active model: {active_model}")

    prompt = (
        f"List the current top 5 standings for {target}. "
        "Format: 'Rank. Team: Record (Pts/GB)'. "
        "No intro. No conversational filler. Just the list."
    )
    
    response = None
    try:
        print(f"🔍 Fetching data...")
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
    except Exception as e:
        print(f"⚠️ Search Attempt Failed: {e}")
        print("🔄 Trying fallback to internal memory without search tool...")
        try:
            response = client.models.generate_content(
                model=active_model,
                contents=prompt + " (Use your internal knowledge)."
            )
        except Exception as e2:
            print(f"❌ Critical Error: Both attempts failed. {e2}")
            return

    if response and response.text:
        try:
            standings_text = response.text.strip()
            tz = pytz.timezone('America/Chicago')
            timestamp = datetime.now(tz).strftime("%I:%M %p CT")
            
            league_tag = target.split(' ')[0]
            tweet_text = f"📊 {target} Standings\n\n{standings_text}\n\n🕒 {timestamp}\n#{league_tag} #SportsUpdates"
            
            X_CLIENT.create_tweet(text=tweet_text, user_auth=True)
            print(f"🚀 Success! Posted {target} to X.")
            
        except Exception as post_err:
            print(f"❌ X API Error: {post_err}")
    else:
        print("❌ Model failed to return text.")

if __name__ == "__main__":
    run()