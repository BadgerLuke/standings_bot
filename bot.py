import tweepy
import requests
import random
import os
import datetime

# --- AUTHENTICATION ---
X_CLIENT = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_SECRET")
)
SPORTS_KEY = os.getenv("SPORTS_API_KEY")

POOL = [
    {"name": "NHL Atlantic", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic"},
    {"name": "NHL Metropolitan", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Metropolitan"},
    {"name": "NBA Atlantic", "id": 12, "sport": "nba", "domain": "v1.basketball", "target": "Atlantic"},
    {"name": "MLS Eastern", "id": 253, "sport": "soccer", "domain": "v3.football", "target": "Eastern"}
]

def get_current_season(domain, league_id):
    """Asks the API which season is actually active right now."""
    url = f"https://{domain}.api-sports.io/leagues"
    try:
        res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params={"id": league_id})
        data = res.json()
        for season in data['response'][0]['seasons']:
            if season['current'] == True:
                return season['year']
    except:
        return datetime.datetime.now().year - 1
    return datetime.datetime.now().year - 1

def fetch_standings(choice):
    season = get_current_season(choice['domain'], choice['id'])
    url = f"https://{choice['domain']}.api-sports.io/standings"
    
    print(f"🚀 Fetching {choice['name']} | League {choice['id']} | Season {season}")
    
    try:
        res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params={"league": choice['id'], "season": season})
        res_data = res.json()
        
        if not res_data.get('response'):
            print(f"⚠️ API returned no response for season {season}")
            return None
        
        # Standard API-Sports structure: response[0] contains the standings
        raw_data = res_data['response'][0]
        # Some APIs (like Hockey) nest this further under 'league' -> 'standings'
        standings = raw_data.get('league', {}).get('standings', raw_data)

        # 1. Look for Nested Division Lists
        if isinstance(standings[0], list):
            for group in standings:
                group_name = group[0].get('group', {}).get('name', '')
                if choice['target'].lower() in group_name.lower():
                    return group
            # Fallback: if we can't find the division, just take the first group available
            return standings[0]
            
        # 2. Look for Flat Lists (NBA often uses this)
        return standings
                
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return None

def format_row(sport, t):
    try:
        name = t['team']['name']
        if sport == "hockey":
            # Accessing keys safely for 2026 schema
            w = t['games']['win']['total']
            l = t['games']['lose']['total']
            ot = t['games']['lose'].get('ot', 0)
            return f"{name}: {w}-{l}-{ot} ({t['points']}pts)"
        
        w = t.get('won', t.get('wins', {}).get('total', 0))
        l = t.get('lost', t.get('losses', {}).get('total', 0))
        return f"{name}: {w}-{l}"
    except:
        return "Data unavailable"

def run_bot():
    choice = random.choice(POOL)
    data = fetch_standings(choice)
    
    if not data or not isinstance(data, list):
        print("❌ Final Result: Could not parse standings data.")
        return
    
    tweet = f"📊 {choice['name']} Standings\n\n"
    # Take the top 5 teams
    for i, team in enumerate(data[:5], 1):
        row = format_row(choice['sport'], team)
        tweet += f"{i}. {row}\n"
    
    tweet += f"\n#Sports #{choice['sport'].upper()}"
    
    try:
        X_CLIENT.create_tweet(text=tweet)
        print(f"✅ SUCCESSFULLY POSTED TO X!")
    except Exception as e:
        print(f"❌ X Posting Error: {e}")

if __name__ == "__main__":
    run_bot()