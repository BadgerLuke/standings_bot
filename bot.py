import tweepy
import requests
import random
import os

# --- AUTH ---
X_CLIENT = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_SECRET")
)
SPORTS_KEY = os.getenv("SPORTS_API_KEY")

# Updated Pool with corrected IDs for 2026
POOL = [
    {"name": "NHL Atlantic", "id": 3, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic"},
    {"name": "NHL Metropolitan", "id": 3, "sport": "hockey", "domain": "v1.hockey", "target": "Metropolitan"},
    {"name": "NHL Central", "id": 3, "sport": "hockey", "domain": "v1.hockey", "target": "Central"},
    {"name": "NHL Pacific", "id": 3, "sport": "hockey", "domain": "v1.hockey", "target": "Pacific"},
    {"name": "NBA Eastern", "id": 12, "sport": "nba", "domain": "v1.basketball", "target": "East"},
    {"name": "NBA Western", "id": 12, "sport": "nba", "domain": "v1.basketball", "target": "West"}
]

def fetch_data(choice):
    # For March 2026, the current NHL/NBA season started in 2025
    season = 2025 
    url = f"https://{choice['domain']}.api-sports.io/standings"
    
    print(f"📡 Requesting {choice['name']} | League ID: {choice['id']} | Season: {season}")
    
    try:
        res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params={"league": choice['id'], "season": season})
        json_data = res.json()

        # --- DEBUG: Print the structure if empty ---
        if not json_data.get('response'):
            print(f"❌ API Error/Empty: {json_data.get('errors')}")
            return None

        # API-Sports often wraps standings differently per sport
        # Hockey: response[0]['league']['standings']
        # Basketball: response[0]
        raw_response = json_data['response']
        
        # Try to find the list of teams in the three most common spots
        standings = None
        if isinstance(raw_response[0], list): # Flat list
            standings = raw_response[0]
        elif 'league' in raw_response[0]: # Hockey style
            standings = raw_response[0]['league'].get('standings', raw_response[0])
        else:
            standings = raw_response[0]

        # Handle Nested Divisions (List of Lists)
        if isinstance(standings[0], list):
            for group in standings:
                # Check the first team's group name
                group_name = group[0].get('group', {}).get('name', '')
                if choice['target'].lower() in group_name.lower():
                    return group
            return standings[0] # Fallback
            
        return standings
    except Exception as e:
        print(f"⚠️ Fetch logic error: {e}")
        return None

def run():
    choice = random.choice(POOL)
    data = fetch_data(choice)
    
    if not data:
        print("⛔ No data could be parsed. Check the ID and Season.")
        return

    tweet = f"📊 {choice['name']} Standings\n\n"
    for i, team in enumerate(data[:5], 1):
        name = team['team']['name']
        try:
            if choice['sport'] == "hockey":
                # NHL v1 Stat Path
                w = team['games']['win']['total']
                l = team['games']['lose']['total']
                ot = team['games']['lose'].get('ot', 0)
                tweet += f"{i}. {name}: {w}-{l}-{ot} ({team['points']}pts)\n"
            else:
                w = team.get('won', team.get('wins', {}).get('total', 0))
                l = team.get('lost', team.get('losses', {}).get('total', 0))
                tweet += f"{i}. {name}: {w}-{l}\n"
        except:
            tweet += f"{i}. {name}: Data Pending\n"

    tweet += f"\n#SportsData #{choice['sport'].upper()}"
    
    try:
        X_CLIENT.create_tweet(text=tweet)
        print("🚀 SUCCESS! Posted to X.")
    except Exception as e:
        print(f"❌ X.com Error: {e}")

if __name__ == "__main__":
    run()