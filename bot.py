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
    {"name": "NHL Atlantic", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic Division"},
    {"name": "NHL Metropolitan", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Metropolitan Division"},
    {"name": "NBA Atlantic", "id": 12, "sport": "nba", "domain": "v1.basketball", "target": "Atlantic"},
    {"name": "MLS Eastern", "id": 253, "sport": "soccer", "domain": "v3.football", "target": "Eastern Conference"}
]

def fetch_standings(choice):
    url = f"https://{choice['domain']}.api-sports.io/standings"
    current_year = datetime.datetime.now().year
    
    # We try the current year first, then the previous year if current is empty
    seasons_to_try = [current_year, current_year - 1]
    
    for season in seasons_to_try:
        try:
            print(f"Checking {choice['name']} for season {season}...")
            res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params={"league": choice['id'], "season": season})
            res_data = res.json()
            
            # CRITICAL FIX: Check if 'response' has data
            if not res_data.get('response'):
                continue 
            
            data = res_data['response'][0]
            standings = data.get('league', {}).get('standings', data)
            
            # Handle nested lists (standard for most divisions)
            if standings and isinstance(standings[0], list):
                for group in standings:
                    group_name = group[0].get('group', {}).get('name', '')
                    if choice['target'].lower() in group_name.lower():
                        return group
            
            if standings:
                return standings
                
        except Exception as e:
            print(f"Skipping {season} due to error: {e}")
            continue
            
    return None

def format_row(sport, t):
    name = t['team']['name']
    if sport == "hockey":
        w, l, ot = t['games']['win']['total'], t['games']['lose']['total'], t['games']['lose'].get('ot', 0)
        return f"{name}: {w}-{l}-{ot} ({t['points']}pts)"
    elif sport == "soccer":
        return f"{name}: {t['points']}pts ({t['all']['win']}-{t['all']['draw']}-{t['all']['lose']})"
    
    # NBA/NFL default
    w = t.get('won', t.get('wins', {}).get('total', 0))
    l = t.get('lost', t.get('losses', {}).get('total', 0))
    return f"{name}: {w}-{l}"

def run_bot():
    choice = random.choice(POOL)
    data = fetch_standings(choice)
    
    if not data:
        print("❌ Final Result: No data found for any season.")
        return
    
    tweet = f"📊 {choice['name']} Standings\n\n"
    for i, team in enumerate(data[:5], 1):
        tweet += f"{i}. {format_row(choice['sport'], team)}\n"
    
    tweet += f"\n#SportsData #{choice['name'].replace(' ', '')}"
    X_CLIENT.create_tweet(text=tweet)
    print(f"✅ Success: Posted {choice['name']}")

if __name__ == "__main__":
    run_bot()