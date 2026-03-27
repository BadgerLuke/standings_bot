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

POOL = [
    {"name": "NHL Atlantic", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic"},
    {"name": "NHL Metropolitan", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Metropolitan"},
    {"name": "NHL Central", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Central"},
    {"name": "NHL Pacific", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Pacific"},
]

def fetch_data(choice):
    season = 2025 
    url = f"https://{choice['domain']}.api-sports.io/standings"
    params = {"league": choice['id'], "season": season}
    headers = {"x-apisports-key": SPORTS_KEY}
    
    try:
        res = requests.get(url, headers=headers, params=params)
        json_data = res.json()
        
        # Get the main response list
        raw_response = json_data.get('response', [])
        
        if not raw_response:
            print(f"⚠️ No data returned for {choice['name']}")
            return None

        # Logic Fix: Iterate through ALL items in response to find the target division
        for division_item in raw_response:
            # The structure can be a list of teams or a nested list
            current_group = division_item
            if isinstance(division_item, list) and len(division_item) > 0:
                # Check the first team's group name
                group_info = division_item[0].get('group', {})
                group_name = group_info.get('name', '')
                
                if choice['target'].lower() in group_name.lower():
                    print(f"✅ Matched {choice['target']} in {group_name}")
                    return division_item

        print(f"❓ Target '{choice['target']}' not found. Available groups were checked.")
        return None

    except Exception as e:
        print(f"⛔ Error fetching/parsing: {e}")
        return None

def run():
    choice = random.choice(POOL)
    data = fetch_data(choice)
    
    if not data:
        print("⏭️ Skipping tweet due to missing data.")
        return

    # Sort teams by their current rank
    data.sort(key=lambda x: x.get('position', x.get('rank', 99)))

    tweet = f"📊 {choice['name']} Standings\n\n"
    for i, team in enumerate(data[:5], 1):
        name = team['team']['name']
        w = team['games']['win']['total']
        l = team['games']['lose']['total']
        ot = team['games']['lose'].get('ot', 0)
        pts = team.get('points', 0)
        tweet += f"{i}. {name}: {w}-{l}-{ot} ({pts}pts)\n"

    # Add unique timestamp for X.com duplicate protection
    tz = pytz.timezone('America/Chicago')
    now = datetime.now(tz).strftime("%I:%M %p CT")
    tweet += f"\n🕒 Updated: {now}\n#NHL #StandingsBot"

    try:
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Successfully posted {choice['name']} at {now}")
    except Exception as e:
        print(f"❌ X.com Error: {e}")

if __name__ == "__main__":
    run()