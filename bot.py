import os
import random
import tweepy
from google import genai
from google.genai import types
from datetime import datetime, date
import pytz
import re
import tempfile
from PIL import Image, ImageDraw, ImageFont

# --- API SETUP ---
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

X_CLIENT = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

# v1 API required for media uploads
X_AUTH = tweepy.OAuth1UserHandler(
    os.environ.get("X_API_KEY"),
    os.environ.get("X_API_SECRET"),
    os.environ.get("X_ACCESS_TOKEN"),
    os.environ.get("X_ACCESS_SECRET")
)
X_API_V1 = tweepy.API(X_AUTH)

# --- CONFIGURATION ---
NBA_COMMUNITY_ID = "1510261147114516482"
PREFERRED_MODEL = "gemini-3-flash-preview"

ALL_DIVISIONS = [
    "NHL Central Division", "NHL Pacific Division", "NHL Atlantic Division", "NHL Metropolitan Division",
    "NBA Atlantic Division", "NBA Central Division", "NBA Southeast Division", "NBA Northwest Division", "NBA Pacific Division", "NBA Southwest Division",
    "MLB AL East", "MLB AL Central", "MLB AL West", "MLB NL East", "MLB NL Central", "MLB NL West",
    "MLS Eastern Conference", "MLS Western Conference"
]

# Approximate regular season windows (month, day). Ranges that cross Dec 31 are handled automatically.
REGULAR_SEASON_WINDOWS = {
    "NHL": ((10, 8),  (4, 18)),   # Oct 8 – Apr 18
    "NBA": ((10, 20), (4, 15)),   # Oct 20 – Apr 15
    "MLB": ((3, 27),  (9, 29)),   # Mar 27 – Sep 29
    "MLS": ((2, 22),  (10, 20)),  # Feb 22 – Oct 20
}

def _in_regular_season(league, today: date) -> bool:
    start_md, end_md = REGULAR_SEASON_WINDOWS[league]
    start = date(today.year, start_md[0], start_md[1])
    end   = date(today.year, end_md[0],   end_md[1])
    if start <= end:
        return start <= today <= end
    # Range wraps across year boundary (e.g. Oct–Apr)
    return today >= start or today <= end

def get_active_divisions(today: date) -> list:
    active = [lg for lg in REGULAR_SEASON_WINDOWS if _in_regular_season(lg, today)]
    print(f"Leagues in regular season: {active if active else 'none — falling back to all'}")
    if not active:
        return ALL_DIVISIONS
    return [div for div in ALL_DIVISIONS if any(div.startswith(lg) for lg in active)]

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_PATHS_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arial.ttf",
]

def load_font(paths, size):
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def create_standings_image(title, date_label, standings_lines, time_str, league_tag):
    WIDTH = 860
    H_PAD = 44
    ROW_HEIGHT = 48
    HEADER_HEIGHT = 110
    FOOTER_HEIGHT = 54

    lines = [l for l in standings_lines if l.strip()]
    HEIGHT = HEADER_HEIGHT + len(lines) * ROW_HEIGHT + FOOTER_HEIGHT + 20

    # Color palette
    BG = (13, 17, 30)
    HEADER_BG = (22, 55, 140)
    ROW_A = (24, 32, 52)
    ROW_B = (18, 24, 40)
    WHITE = (255, 255, 255)
    GOLD = (250, 189, 40)
    LIGHT_GRAY = (180, 190, 210)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    font_title = load_font(FONT_PATHS, 30)
    font_sub   = load_font(FONT_PATHS_REGULAR, 19)
    font_row   = load_font(FONT_PATHS, 21)
    font_foot  = load_font(FONT_PATHS_REGULAR, 16)

    # Header bar
    draw.rectangle([0, 0, WIDTH, HEADER_HEIGHT], fill=HEADER_BG)
    draw.text((H_PAD, 18), title, font=font_title, fill=WHITE)
    draw.text((H_PAD, 62), date_label, font=font_sub, fill=GOLD)
    # Gold accent line below header
    draw.rectangle([0, HEADER_HEIGHT, WIDTH, HEADER_HEIGHT + 3], fill=GOLD)

    # Standings rows
    y = HEADER_HEIGHT + 3
    for i, line in enumerate(lines):
        row_bg = ROW_A if i % 2 == 0 else ROW_B
        draw.rectangle([0, y, WIDTH, y + ROW_HEIGHT - 1], fill=row_bg)
        draw.text((H_PAD, y + 12), line, font=font_row, fill=WHITE)
        y += ROW_HEIGHT

    # Footer
    footer_y = HEIGHT - FOOTER_HEIGHT
    draw.rectangle([0, footer_y - 2, WIDTH, HEIGHT], fill=(8, 11, 20))
    draw.rectangle([0, footer_y - 2, WIDTH, footer_y], fill=GOLD)
    foot_text = f"{time_str}  |  #{league_tag} #SportsStandings #SportsUpdates"
    draw.text((H_PAD, footer_y + 12), foot_text, font=font_foot, fill=LIGHT_GRAY)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, "PNG", optimize=True)
    tmp.close()
    return tmp.name


def run():
    tz = pytz.timezone("America/Chicago")
    now = datetime.now(tz)
    date_label = now.strftime("%B %d, %Y")

    active_divisions = get_active_divisions(now.date())
    target = random.choice(active_divisions)
    print(f"Target: {target}")

    season = "2026" if any(x in target for x in ["MLB", "MLS"]) else "2025-26"
    prompt = (
        f"Full current standings for {target} {season}. Today is {date_label}. "
        f"Use Google Search. List every team ranked in order. "
        f"Format each line exactly as: Rank. Team Name: W-L (or W-L-OTL for NHL). "
        f"No intro sentence, no outro, no footnotes, no markdown."
    )

    # --- AUTO-DISCOVERY MODEL LOGIC ---
    working_model = PREFERRED_MODEL
    try:
        client.models.get(model=PREFERRED_MODEL)
    except Exception:
        available = [m.name for m in client.models.list() if "flash" in m.name.lower()]
        working_model = available[0].replace("models/", "") if available else None

    if not working_model:
        print("No available models found.")
        return

    try:
        response = client.models.generate_content(
            model=working_model,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        )

        if not (response and response.text):
            print("No content generated.")
            return

        clean_text = re.sub(r"\[\d+\]", "", response.text.strip())
        standings_lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
        league_tag = target.split(" ")[0]
        time_str = now.strftime("%I:%M %p CT").lstrip("0")

        # Build image
        image_path = create_standings_image(
            title=f"{target} Standings",
            date_label=date_label,
            standings_lines=standings_lines,
            time_str=time_str,
            league_tag=league_tag,
        )
        print(f"Image saved: {image_path}")

        # Short tweet text to accompany the image
        tweet_text = f"{target} Standings ({date_label})\n\n#{league_tag} #SportsStandings"

        # Upload image via v1 API
        print("Uploading image...")
        media = X_API_V1.media_upload(filename=image_path)
        media_id = media.media_id

        # Post to main feed
        print("Posting to main feed...")
        X_CLIENT.create_tweet(text=tweet_text, media_ids=[media_id], user_auth=True)

        # Cross-post to NBA Community if applicable
        if "NBA" in target:
            print(f"NBA target detected. Cross-posting to Community {NBA_COMMUNITY_ID}...")
            try:
                X_CLIENT.create_tweet(
                    text=tweet_text,
                    media_ids=[media_id],
                    community_id=NBA_COMMUNITY_ID,
                    user_auth=True
                )
            except Exception as comm_err:
                print(f"Community post failed: {comm_err}")

        # Clean up temp file
        os.unlink(image_path)
        print("SUCCESS!")

    except Exception as e:
        print(f"Execution error: {e}")


if __name__ == "__main__":
    run()
