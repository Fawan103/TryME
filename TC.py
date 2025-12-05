import streamlit as st
import requests
from datetime import datetime, timedelta
import re

# ===================================
# YOUTUBE API CONFIG
# ===================================
API_KEY = "AIzaSyBEkDgN8rmggrbgRSxGznLwrJKkrccWFi0"

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# ===================================
# STREAMLIT UI
# ===================================
st.set_page_config(page_title="Wild West Viral Topics Tool", layout="wide")
st.title("🤠 Wild West History Viral Topics Tool")

days = st.number_input("Enter Days to Search (1–30)", 1, 30, 5)

# ===================================
# WILD WEST / OLD WEST KEYWORDS
# ===================================
keywords = [
    "wild west history",
    "american old west",
    "american frontier history",
    "old west outlaws",
    "famous gunslingers",
    "wild west cowboys",
    "cowboys and outlaws",
    "lawmen of the old west",
    "wild west sheriffs",
    "duels in the wild west",
    "gunfights in the old west",
    "tombstone arizona history",
    "ok corral gunfight",
    "billy the kid history",
    "jesse james history",
    "wyatt earp documentary",
    "doc holliday story",
    "wild bill hickok history",
    "buffalo bill cody history",
    "apache wars history",
    "native americans and the frontier",
    "indian wars american west",
    "frontier forts of the west",
    "gold rush history",
    "california gold rush story",
    "klondike gold rush history",
    "wagon trains and pioneers",
    "oregon trail history",
    "homesteaders in the west",
    "mountain men history",
    "trappers and fur trade",
    "frontier life in the 1800s",
    "railroads and the wild west",
    "transcontinental railroad history",
    "stagecoach robberies",
    "wild west saloons",
    "boomtowns of the old west",
    "ghost towns in the american west",
    "texas rangers history",
    "range wars in the west",
    "cattle drives and cowboys",
    "native american perspective wild west",
    "myths of the wild west",
    "real stories of the old west",
    "untold stories of the frontier",
    "women of the wild west",
    "famous women in the old west",
    "wild west legends and lore",
    "american west documentary",
    "frontier justice in the old west",
    "outlaw gangs of the west"
]

# ===================================
# HELPER — ISO DURATION TO MINUTES
# ===================================
def iso_to_minutes(iso):
    if not iso:
        return 0.0
    h = m = s = 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if match:
        h = int(match.group(1)) if match.group(1) else 0
        m = int(match.group(2)) if match.group(2) else 0
        s = int(match.group(3)) if match.group(3) else 0
    return round((h * 3600 + m * 60 + s) / 60, 1)

# ===================================
# MAIN
# ===================================
if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"

        results = []

        for keyword in keywords:
            st.write(f"🔍 Searching: {keyword}")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "relevanceLanguage": "en",   # English focus
                "key": API_KEY
            }

            search_resp = requests.get(SEARCH_URL, params=search_params)
            if search_resp.status_code != 200:
                continue

            items = search_resp.json().get("items", [])
            if not items:
                continue

            video_ids = [
                i["id"]["videoId"]
                for i in items
                if i.get("id", {}).get("videoId")
            ]

            channel_ids = [
                i["snippet"]["channelId"]
                for i in items
                if i.get("snippet", {}).get("channelId")
            ]

            if not video_ids or not channel_ids:
                continue

            # ===================
            # VIDEO DATA
            # ===================
            video_resp = requests.get(
                VIDEO_URL,
                params={
                    "part": "statistics,contentDetails",
                    "id": ",".join(video_ids),
                    "key": API_KEY,
                }
            )
            if video_resp.status_code != 200:
                continue

            video_lookup = {
                v["id"]: v
                for v in video_resp.json().get("items", [])
            }

            # ===================
            # CHANNEL DATA
            # ===================
            channel_resp = requests.get(
                CHANNEL_URL,
                params={
                    "part": "statistics",
                    "id": ",".join(channel_ids),
                    "key": API_KEY,
                }
            )
            if channel_resp.status_code != 200:
                continue

            channel_lookup = {
                c["id"]: c
                for c in channel_resp.json().get("items", [])
            }

            # ===================
            # FILTER PIPELINE
            # ===================
            for item in items:
                vid = item["id"]["videoId"]
                cid = item["snippet"]["channelId"]

                if vid not in video_lookup or cid not in channel_lookup:
                    continue

                v_obj = video_lookup.get(vid, {})
                c_obj = channel_lookup.get(cid, {})

                # ---- Duration safety
                content_details = v_obj.get("contentDetails", {})
                dur_iso = content_details.get("duration")
                if not dur_iso:
                    continue

                duration_min = iso_to_minutes(dur_iso)
                # ✅ Duration 10+ minutes
                if duration_min < 10:
                    continue

                # ---- Statistics safety
                v_stats = v_obj.get("statistics", {})
                c_stats = c_obj.get("statistics", {})

                try:
                    views = int(v_stats.get("viewCount", 0))
                except (TypeError, ValueError):
                    views = 0

                try:
                    subs = int(c_stats.get("subscriberCount", 0))
                except (TypeError, ValueError):
                    subs = 0

                # ✅ Views ≥ 2,000
                if views < 2000:
                    continue

                # ✅ Subscribers ≥ 1,000 (no upper cap)
                if subs < 1000:
                    continue

                results.append({
                    "Keyword": keyword,
                    "Title": item["snippet"]["title"],
                    "Duration": f"{duration_min} min",
                    "Views": views,
                    "Subscribers": subs,
                    "URL": f"https://www.youtube.com/watch?v={vid}",
                    "Description": item["snippet"].get("description", "")
                })

        # ===================
        # DISPLAY
        # ===================
        if results:
            results.sort(key=lambda x: x["Views"], reverse=True)

            st.success(f"✅ Found {len(results)} Wild West history candidates")

            for r in results:
                st.markdown(f"""
---
## 🤠 {r['Title']}
**Keyword:** {r['Keyword']}  
⏱ Duration: **{r['Duration']}**  
👁 Views: **{r['Views']:,}**  
👥 Subscribers: **{r['Subscribers']:,}**

🔗 [Watch Video]({r['URL']})

{r['Description']}
""")
        else:
            st.warning("No qualifying Wild West videos found with current filters.")

    except Exception as e:
        st.error(f"❌ Runtime Error: {e}")
