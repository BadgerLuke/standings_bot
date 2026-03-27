import os
import random
import requests
import tweepy
from datetime import datetime
import pytz

# --- CONFIGURATION ---
X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

SPORTS_KEY = os.environ.get("SPORTS_API_KEY")

# NHL ID is 57 for API-Sports Hockey v1
# 'target' must match the API's group name (e.g. "Pacific Division")
POOL = [
    {"name": "NHL Atlantic", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic"},
    {"name": "NHL Metropolitan", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Metropolitan"},
    {"name": "NHL Central", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Central"},
    {"name": "NHL Pacific", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Pacific"},
]

def fetch_data(choice):
    season = 2025 # Current 2025-26 Season
    url = f"https://{choice['domain']}.api-sports.io/standings"
    params = {"league": choice['id'], "season": season}
    headers = {"x-apisports-key": SPORTS_KEY}
    
    try:
        res = requests.get(url, headers=headers, params=params)
        json_data = res.json()
        
        # API-Sports NHL response is a list of lists: response[0] contains 4 lists (divisions)
        all_divisions = json_data.get('response', [[]])[0]
        
        # We search specifically for the division matching our target
        for division in all_divisions:
            # Check the group name for each division
            group_name = division[0].get('group', {}).get('name', '')
            if choice['target'].lower() in group_name.lower():
                print(f"✅ Found correct teams for {choice['target']}")
                return division
        
        print(f"⚠️ Could not find exact match for {choice['target']}, using first available.")
        return all_divisions[0]
    except Exception as e:
        print(f"⛔ Error fetching/parsing: {e}")
        return None

def run():
    choice = random.choice(POOL)
    data = fetch_data(choice)
    
    if not data:
        return

    # Create the Tweet
    tweet = f"📊 {choice['name']} Standings\n\n"
    
    # Sort by rank just in case
    data.sort(key=lambda x: x.get('position', x.get('rank', 0)))

    for i, team in enumerate(data[:5], 1):
        name = team['team']['name']
        w = team['games']['win']['total']
        l = team['games']['lose']['total']
        ot = team['games']['lose'].get('ot', 0)
        pts = team.get('points', 0)
        tweet += f"{i}. {name}: {w}-{l}-{ot} ({pts}pts)\n"

    # Add unique timestamp to avoid "Duplicate Tweet" error
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz).strftime("%I:%M %p CT")
    tweet += f"\n🕒 Updated: {now}\n#NHL #SportsData"

    try:
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Posted: {choice['name']} at {now}")
    except Exception as e:
        print(f"❌ X.com Error: {e}")

if __name__ == "__main__":
    run()