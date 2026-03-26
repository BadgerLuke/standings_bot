import tweepy
import requests
import random
import os
import datetime

# --- CREDENTIALS ---
X_AUTH = {
    "key": os.getenv("X_API_KEY"),
    "secret": os.getenv("X_API_SECRET"),
    "token": os.getenv("X_ACCESS_TOKEN"),
    "token_secret": os.getenv("X_ACCESS_SECRET")
}
SPORTS_KEY = os.getenv("SPORTS_API_KEY")

# --- LEAGUE POOL ---
POOL = [
    {"name": "NHL Atlantic", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Atlantic Division"},
    {"name": "NHL Metropolitan", "id": 57, "sport": "hockey", "domain": "v1.hockey", "target": "Metropolitan Division"},
    {"name": "NFL AFC North", "id": 1, "sport": "nfl", "domain": "v1.american-football", "target": "AFC North"},
    {"name": "NBA Atlantic", "id": 12, "sport": "nba", "domain": "v1.basketball", "target": "Atlantic"}
]

class SportsBot:
    def __init__(self):
        self.client = tweepy.Client(
            consumer_key=X_AUTH["key"], consumer_secret=X_AUTH["secret"],
            access_token=X_AUTH["token"], access_token_secret=X_AUTH["token_secret"]
        )
    
    def get_standings(self, choice):
        url = f"https://{choice['domain']}.api-sports.io/standings"
        season = datetime.datetime.now().year if datetime.datetime.now().month > 7 else datetime.datetime.now().year - 1
        res = requests.get(url, headers={"x-apisports-key": SPORTS_KEY}, params={"league": choice['id'], "season": season})
        data = res.json()['response'][0]
        standings = data.get('league', {}).get('standings', data)
        
        if isinstance(standings[0], list):
            for group in standings:
                if choice['target'].lower() in group[0].get('group', {}).get('name', '').lower():
                    return group
        return standings

    def format_line(self, sport, t):
        name = t['team']['name']
        if sport == "hockey":
            w, l, ot = t['games']['win']['total'], t['games']['lose']['total'], t['games']['lose'].get('ot', 0)
            return f"{name}: {w}-{l}-{ot} ({t['points']}pts)"
        w = t.get('won', t.get('wins', {}).get('total', 0))
        l = t.get('lost', t.get('losses', {}).get('total', 0))
        return f"{name}: {w}-{l}"

    def post(self):
        choice = random.choice(POOL)
        data = self.get_standings(choice)
        if not data: return
        
        tweet = f"📊 {choice['name']} Standings\n\n"
        for i, team in enumerate(data[:5], 1):
            tweet += f"{i}. {self.format_line(choice['sport'], team)}\n"
        
        self.client.create_tweet(text=tweet)
        print(f"Posted: {choice['name']}")

if __name__ == "__main__":
    SportsBot().post()