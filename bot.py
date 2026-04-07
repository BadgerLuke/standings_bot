# --- UPDATE THIS SECTION IN bot.py ---

def run():
    division = random.choice(POOL)
    print(f"🤖 Searching Google for {division}...")

    prompt = (
        f"Give me the current top 5 standings for the {division} for the 2025-26 season. "
        "Format exactly as a list: 'Rank. Team: W-L-OTL (Points)'. No intro text."
    )
    
    try:
        # CHANGED: model="gemini-1.5-flash" (The stable free-tier workhorse)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool]
            )
        )
        
        # Check if the response actually has text (sometimes safety filters block sports data)
        if not response.text:
            print("⚠️ Gemini returned an empty response. Likely a safety filter trigger.")
            return

        standings_text = response.text.strip()
        
        # Timestamp logic...
        tz = pytz.timezone('America/Chicago')
        timestamp = datetime.now(tz).strftime("%I:%M %p CT")
        
        tweet = f"📊 {division} Standings\n\n{standings_text}\n\n🕒 Updated: {timestamp}\n#NHL"
        
        X_CLIENT.create_tweet(text=tweet)
        print(f"🚀 Posted {division} successfully.")
        
    except Exception as e:
        # If it still says 429, it means your "Search" tool is blocked on the anonymous tier
        print(f"❌ Error: {e}")