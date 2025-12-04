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
st.set_page_config(page_title="YouTube Viral Topics Tool", layout="wide")
st.title("📊 YouTube Viral Topics Tool")

days = st.number_input("Enter Days to Search (1–30)", 1, 30, 5)

# ===================================
# KEYWORDS
# ===================================
keywords = [
    "Reality hack","consciousness hack","words shape reality","power of language",
    "mind conditioning","brain reprogramming","social programming","break the matrix",
    "layers of existence","levels of reality","hidden dimensions","multidimensional consciousness",
    "existential freedom","burden of freedom","existential crisis","search for meaning",
    "purpose of life","why we exist","illusion of time","time is not real","memory and identity",
    "who am I really","ego death","self identity","consciousness and brain","neurophilosophy",
    "manifestation science","divine power within","inner god","self mastery",
    "law of attraction explained","quantum consciousness","observer effect reality",
    "frequency and vibration","ancient wisdom modern science","esoteric philosophy",
    "mystical philosophy","hermetic teachings","secret knowledge","forgotten wisdom",
    "spiritual awakening","dark night of the soul","shadow self","collective unconscious",
    "jungian psychology","philosophy of meaning","nihilism explained","anxiety and the void",
    "fear of existence","self liberation","transcendence","reality and perception",
    "simulation theory","free will vs fate","destiny versus choice","power of belief",
    "subconscious mind","reprogramming reality","emotional conditioning","mental alchemy",
    "higher self awakening","cosmic consciousness","awakening consciousness"
]

# ===================================
# HELPER — ISO DURATION TO MINUTES
# ===================================
def iso_to_minutes(iso):
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
                "relevanceLanguage": "en",
                "key": API_KEY
            }

            search_data = requests.get(SEARCH_URL, params=search_params).json()

            items = search_data.get("items", [])
            if not items:
                continue

            video_ids = [i["id"]["videoId"] for i in items]
            channel_ids = [i["snippet"]["channelId"] for i in items]

            # ===================
            # VIDEO DATA
            # ===================
            video_data = requests.get(
                VIDEO_URL,
                params={
                    "part": "statistics,contentDetails",
                    "id": ",".join(video_ids),
                    "key": API_KEY,
                }
            ).json()

            video_lookup = {v["id"]: v for v in video_data.get("items", [])}

            # ===================
            # CHANNEL DATA
            # ===================
            channel_data = requests.get(
                CHANNEL_URL,
                params={
                    "part": "statistics",
                    "id": ",".join(channel_ids),
                    "key": API_KEY,
                }
            ).json()

            channel_lookup = {c["id"]: c for c in channel_data.get("items", [])}

            # ===================
            # FILTER PIPELINE
            # ===================
            for item in items:

                vid = item["id"]["videoId"]
                cid = item["snippet"]["channelId"]

                if vid not in video_lookup or cid not in channel_lookup:
                    continue

                # -------- VIDEO LENGTH
                duration_min = iso_to_minutes(
                    video_lookup[vid]["contentDetails"]["duration"]
                )

                if duration_min < 15:
                    continue

                # -------- STATS
                views = int(video_lookup[vid]["statistics"].get("viewCount", 0))
                subs = int(channel_lookup[cid]["statistics"].get("subscriberCount", 0))

                # ✅ NEW FILTERS
                if views < 2000:
                    continue

                if subs < 50000 or subs > 70000:
                    continue

                # -------- ADD RESULT
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

            st.success(f"✅ Found {len(results)} high-quality viral candidates")

            for r in results:
                st.markdown(f"""
---
## 🔥 {r['Title']}
**Keyword:** {r['Keyword']}  
⏱ Duration: **{r['Duration']}**  
👁 Views: **{r['Views']:,}**  
👥 Subscribers: **{r['Subscribers']:,}**

🔗 [Watch Video]({r['URL']})

{r['Description']}
""")

        else:
            st.warning("No qualifying videos found.")

    except Exception as e:
        st.error(f"❌ Runtime Error: {e}")
