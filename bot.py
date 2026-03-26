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

# Revised Pool: simplified targets for better matching
POOL = [
    {"name": "Western Conference", "id": 3, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic"},
]

def get_live_season(domain, league_id):
    """Hits the leagues endpoint to find the exact string for the active season."""
    url = f"https://{domain}.api-sports.io/leagues"
    try:
        res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params={"id": league_id})
        data = res.json()
        # Look through seasons for the 'current' flag
        for s in data['response'][0]['seasons']:
            if s.get('current') == True:
                return s['year']
        return 2025 # Fallback
    except:
        return 2025

def fetch_data(choice):
    season = get_live_season(choice['domain'], choice['id'])
    url = f"https://{choice['domain']}.api-sports.io/standings"
    
    print(f"📡 Requesting: {choice['name']} | League: {choice['id']} | Season: {season}")
    
    try:
        params = {"league": choice['id'], "season": season}
        res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params=params)
        json_res = res.json()

        if not json_res.get('response'):
            print(f"❌ API literally has no data for {choice['name']} in {season}")
            return None

        # Navigate the response path
        raw = json_res['response'][0]
        # Hockey/NBA usually nest under 'league' or 'standings'
        standings = raw.get('league', {}).get('standings', raw)
        if 'standings' in raw and not isinstance(standings, list):
             standings = raw['standings']

        # If it's a list of lists (Divisions), find our target
        if isinstance(standings[0], list):
            for group in standings:
                # Check team #1 in the group for the division name
                group_name = group[0].get('group', {}).get('name', '')
                if choice['target'].lower() in group_name.lower():
                    return group
            return standings[0] # Fallback to first division found
            
        return standings # Return flat list (NBA/MLS style)

    except Exception as e:
        print(f"⚠️ Fetch Error: {e}")
        return None

def run():
    choice = random.choice(POOL)
    data = fetch_data(choice)
    
    if not data or not isinstance(data, list):
        print("⛔ Script stopped: No list data to format.")
        return

    tweet = f"📊 {choice['name']} Standings\n\n"
    for i, t in enumerate(data[:5], 1):
        name = t['team']['name']
        # Robust stat detection
        try:
            if choice['sport'] == "hockey":
                w = t['games']['win']['total']
                l = t['games']['lose']['total']
                ot = t['games']['lose'].get('ot', 0)
                tweet += f"{i}. {name}: {w}-{l}-{ot} ({t['points']}pts)\n"
            else:
                w = t.get('won', t.get('wins', {}).get('total', 0))
                l = t.get('lost', t.get('losses', {}).get('total', 0))
                tweet += f"{i}. {name}: {w}-{l}\n"
        except:
            tweet += f"{i}. {name}: Data pending\n"

    tweet += f"\n#SportsBot #{choice['sport'].upper()}"
    
    try:
        X_CLIENT.create_tweet(text=tweet)
        print("🚀 SUCCESS: Tweet is live!")
    except Exception as e:
        print(f"❌ X Error: {e}")

if __name__ == "__main__":
    run()