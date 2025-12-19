import streamlit as st
import pandas as pd
from ytmusicapi import YTMusic
import os

# --- 1. GLOBAL MEMORY (The Brain) ---
if 'playing' not in st.session_state:
    st.session_state.playing = {"id": None, "title": "", "artist": "", "playlist": []}
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'fixed_recs' not in st.session_state:
    st.session_state.fixed_recs = []

# --- 2. MASTER STABILITY FUNCTIONS ---
@st.cache_resource
def get_ytm():
    return YTMusic()

def play_engine(vid_id, title, artist, playlist_ids=[]):
    """The core engine that sets the song and prepares the queue"""
    st.session_state.playing = {
        "id": vid_id, 
        "title": title, 
        "artist": artist,
        "playlist": playlist_ids
    }

def handle_mood(tag):
    """Mood Engine: Locks results into memory and starts a playlist"""
    ytm = get_ytm()
    results = ytm.search(tag, filter="songs")
    if results:
        st.session_state.search_results = results
        ids = [t['videoId'] for t in results]
        play_engine(results[0]['videoId'], results[0]['title'], results[0]['artists'][0]['name'], ids)

def handle_fav(title, artist, vid_id):
    """Persistent Favorites Logic"""
    file = 'my_favorites.csv'
    if not os.path.exists(file):
        pd.DataFrame(columns=['Track Name', 'Artist Name(s)', 'VideoID']).to_csv(file, index=False)
    favs = pd.read_csv(file)
    if vid_id not in favs['VideoID'].values:
        new_row = pd.DataFrame([{'Track Name': title, 'Artist Name(s)': artist, 'VideoID': vid_id}])
        favs = pd.concat([favs, new_row], ignore_index=True)
        favs.to_csv(file, index=False)
        st.toast(f"❤️ Saved: {title}")

# --- 1. IMPROVED SEARCH LOGIC ---
def search_and_play_logic(track, artist):
    ytm = get_ytm()
    with st.spinner(f"🔍 Finding {track}..."):
        res = ytm.search(f"{track} {artist} Official Audio", filter="songs")
        if res:
            # ONLY UPDATE THE STATE
            st.session_state.playing = {
                "id": res[0]['videoId'], 
                "title": track, 
                "artist": artist
            }
            # REFRESH TO SHOW THE TOP PLAYER
            st.rerun()


# --- 3. PREMIUM UI & CSS ---
st.set_page_config(page_title="VibeStream Ultimate Pro", page_icon="🎵", layout="wide")

# Corrected CSS to properly hide Streamlit branding
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: white; }
    .player-card { background: #121212; padding: 25px; border-radius: 20px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #1DB954; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #1ed760; transform: scale(1.02); }
    
    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. PERSISTENT PLAYER (WITH AUTO-PLAY NEXT) ---
# --- 4. PERSISTENT PLAYER (FIXED FOR DUPLICATE KEYS) ---
if st.session_state.playing["id"]:
    # We grab the ID to create unique keys
    current_id = st.session_state.playing["id"]
    
    with st.container():
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        col_v, col_i = st.columns([2, 1])
        
        with col_v:
            # We use the standard video player for better audio reliability
            st.video(f"https://www.youtube.com/watch?v={current_id}")
            
        with col_i:
            st.subheader(f"🎶 {st.session_state.playing['title']}")
            st.caption(f"Artist: {st.session_state.playing['artist']}")
            
            # FIXED: We use the current_id to make the key unique every time
            if st.button("❤️ Add to Favorites", key=f"fav_{current_id}"):
                handle_fav(
                    st.session_state.playing['title'], 
                    st.session_state.playing['artist'], 
                    current_id
                )
            
            l_query = f"{st.session_state.playing['title']} {st.session_state.playing['artist']} lyrics".replace(" ", "+")
            st.link_button("📖 View Lyrics", f"https://www.google.com/search?q={l_query}")
            
            # FIXED: Unique key for stop button as well
            if st.button("⏹️ Stop Music", key=f"stop_{current_id}"):
                st.session_state.playing = {"id": None, "title": "", "artist": "", "playlist": []}
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# --- 5. THE FIVE-FEATURE TABS ---
st.title("🚀 VibeStream Ultimate")
tabs = st.tabs(["🔍 Global Search", "🌈 Moods", "📀 My Collection", "❤️ Favorites"])

# TAB 1: SEARCH
with tabs[0]:
    with st.form("search_box"):
        q = st.text_input("Search for any song, artist, or remix...")
        if st.form_submit_button("Search"):
            st.session_state.search_results = get_ytm().search(q, filter="songs")
    
    if st.session_state.search_results:
        cols = st.columns(4)
        all_ids = [t['videoId'] for t in st.session_state.search_results]
        for i, track in enumerate(st.session_state.search_results[:8]):
            with cols[i % 4]:
                st.image(track['thumbnails'][-1]['url'], use_container_width=True)
                st.write(f"**{track['title'][:20]}**")
                st.button("Play", key=f"s_{track['videoId']}", on_click=play_engine, 
                          args=(track['videoId'], track['title'], track['artists'][0]['name'], all_ids[i:]))

# TAB 2: MOODS (100% Stability)
with tabs[1]:
    st.write("### Select your Mood (Auto-Play Enabled)")
    mood_cols = st.columns(4)
    moods = {"💖 Romantic": "Hindi Romantic Hits", "💃 Party": "Bollywood Dance", "☕ Relax": "Hindi Lofi", "😢 Sad": "Sad Melodies"}
    for i, (label, tag) in enumerate(moods.items()):
        mood_cols[i].button(label, key=f"mood_btn_{i}", on_click=handle_mood, args=(tag,))

# TAB 3: COLLECTION (Auto-Detect File)
with tabs[2]:
    possible_files = ['cleaned_music.csv', 'golden_era.csv']
    found_file = next((f for f in possible_files if os.path.exists(f)), None)
    
    if found_file:
        df = pd.read_csv(found_file)
        if not st.session_state.fixed_recs:
            st.session_state.fixed_recs = df.sample(8).to_dict('records')
        
        st.write(f"### From Your Collection ({found_file})")
        c_cols = st.columns(4)
        for i, song in enumerate(st.session_state.fixed_recs):
            with c_cols[i % 4]:
                st.markdown(f"**{song.get('Track Name', 'Unknown')[:20]}**")
                st.caption(song.get('Artist Name(s)', 'Various'))
                if st.button("Listen", key=f"coll_btn_{i}"):
                    search_and_play_logic(song['Track Name'], song['Artist Name(s)'])
        
        if st.button("🔄 Shuffle Collection"):
            st.session_state.fixed_recs = []
            st.rerun()
    else:
        st.error("CSV File not found! Please upload 'golden_era.csv'.")

# TAB 4: FAVORITES
with tabs[3]:
    st.subheader("Your Liked Songs")
    if os.path.exists('my_favorites.csv'):
        fav_df = pd.read_csv('my_favorites.csv')
        if not fav_df.empty:
            for _, row in fav_df.iterrows():
                f1, f2 = st.columns([4, 1])
                f1.write(f"**{row['Track Name']}** — {row['Artist Name(s)']}")
                # Fixed: Use search_and_play_logic here to ensure playable IDs
                if f2.button("Play", key=f"fav_{row['VideoID']}"):
                    search_and_play_logic(row['Track Name'], row['Artist Name(s)'])
        else:
            st.info("No favorites yet!")
    else:
        st.info("No favorites yet!")