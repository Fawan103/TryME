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
                "relevanceLanguage": "en",
                "key": API_KEY
            }

            search_resp = requests.get(SEARCH_URL, params=search_params)
            if search_resp.status_code != 200:
                continue

            items = search_resp.json().get("items", [])
            if not items:
                continue

            video_ids = [i["id"]["videoId"]
                         for i in items if i.get("id", {}).get("videoId")]

            channel_ids = [i["snippet"]["channelId"]
                           for i in items if i.get("snippet", {}).get("channelId")]

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
                if duration_min < 15:
                    continue

                # ---- Statistics safety
                try:
                    views = int(v_obj.get("statistics", {})
                                .get("viewCount", 0))
                except (TypeError, ValueError):
                    views = 0

                try:
                    subs = int(c_obj.get("statistics", {})
                               .get("subscriberCount", 0))
                except (TypeError, ValueError):
                    subs = 0

                # ✅ FILTERS
                if views < 2000:
                    continue

                # ✅ Subscriber MINIMUM only — no maximum limit
                if subs < 50000:
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
