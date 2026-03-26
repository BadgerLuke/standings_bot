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
    
    print(f"📡 Requesting: {choice['name']} | League: {choice['id']} | Season: {season}")
    
    try:
        res = requests.get(url, headers=headers, params=params)
        json_data = res.json()
        
        if not json_data.get('response'):
            print(f"❌ API literally has no data for {choice['name']} in {season}")
            return None

        # The API usually returns response[0] as a list of 4 divisions
        all_groups = json_data['response'][0]
        
        # NHL Specific: The response is a list of lists.
        # We need to find the specific list where 'group' == Target
        if isinstance(all_groups, list) and isinstance(all_groups[0], list):
            for group_list in all_groups:
                # Check the first team in this group to see which division it is
                group_info = group_list[0].get('group', {})
                group_name = group_info.get('name', '')
                
                # If "Central" is in "NHL | Western Conference | Central Division"
                if choice['target'].lower() in group_name.lower():
                    print(f"✅ Found match for {choice['target']} in group: {group_name}")
                    return group_list
            
            print(f"⚠️ Could not find specific group for {choice['target']}. Falling back to first group.")
            return all_groups[0]

        return all_groups
    except Exception as e:
        print(f"⛔ Script stopped: {e}")
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