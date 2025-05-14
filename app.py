import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import random
import pandas as pd
import matplotlib.pyplot as plt

# Database setup
conn = sqlite3.connect('letters.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feeling TEXT,
        message TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# Store password in Streamlit secrets or plain string
PASSWORD = "viewonly123"  # Use only for viewing/searching

# --- Helper Functions ---
def save_letter(feeling, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO letters (feeling, message, timestamp) VALUES (?, ?, ?)', (feeling, message, now))
    conn.commit()

def get_letters():
    c.execute('SELECT * FROM letters ORDER BY timestamp DESC')
    return c.fetchall()

def get_letters_by_feeling(feeling):
    c.execute('SELECT * FROM letters WHERE feeling = ? ORDER BY timestamp DESC', (feeling,))
    return c.fetchall()

def get_random_letter():
    c.execute('SELECT * FROM letters')
    all_letters = c.fetchall()
    return random.choice(all_letters) if all_letters else None

def get_latest_timestamp():
    c.execute('SELECT timestamp FROM letters ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    return datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S") if result else None

def get_feeling_counts():
    df = pd.read_sql_query('SELECT feeling, COUNT(*) as count FROM letters GROUP BY feeling', conn)
    return df

# --- UI ---
st.set_page_config(page_title="Unspoken — Safe Space", page_icon="💌")
st.title("💌 Unspoken — A Safe Place for the Words You Can't Say")

# Reminder Logic
latest_time = get_latest_timestamp()
now = datetime.now()
if (latest_time is None or (now - latest_time).days >= 3 or now.hour >= 18):
    st.info("🕯️ It's a good time to write. Take a moment for yourself.")

# Navigation
page = st.sidebar.radio("Navigate", ["📝 Write a Letter", "🔍 Search by Feeling", "📊 Mood Timeline", "🎲 Random Letter", "🔐 View All (Login)"])

# Page: Write Letter (No login needed)
if page == "📝 Write a Letter":
    st.subheader("Write a New Letter")
    feeling = st.selectbox("Select Feeling", ["Love", "Regret", "Hope", "Anger", "Gratitude", "Sadness", "Other"])
    message = st.text_area("Your Message", height=200)
    if st.button("Save Letter"):
        if message.strip():
            save_letter(feeling, message)
            st.success("Your letter has been saved.")
        else:
            st.warning("Please enter a message.")

# Page: Search
elif page == "🔍 Search by Feeling":
    st.subheader("🔍 Search by Feeling")
    feeling = st.selectbox("Select feeling to explore past letters", ["Love", "Regret", "Hope", "Anger", "Gratitude", "Sadness", "Other"])
    results = get_letters_by_feeling(feeling)
    st.write(f"Found {len(results)} letters tagged with {feeling}")
    for i, (_, f, msg, ts) in enumerate(results):
        st.text_area(f"{f} — {ts}", value=msg, height=150, disabled=True, key=f"search_{i}")

# Page: Mood Timeline
elif page == "📊 Mood Timeline":
    st.subheader("📊 Mood Timeline View")
    df = get_feeling_counts()
    if not df.empty:
        fig, ax = plt.subplots()
        ax.bar(df['feeling'], df['count'], color='skyblue')
        ax.set_ylabel("Number of Letters")
        ax.set_title("Emotions Over Time")
        st.pyplot(fig)
    else:
        st.info("No letters yet to generate timeline.")

# Page: Random Letter
elif page == "🎲 Random Letter":
    st.subheader("🎁 Surprise Letter")
    letter = get_random_letter()
    if letter:
        _, feeling, message, timestamp = letter
        st.write(f"**Feeling:** {feeling} — _{timestamp}_")
        st.text_area("Random Letter", value=message, height=200, disabled=True)
    else:
        st.warning("No letters saved yet.")

# Page: View All (Password Protected)
elif page == "🔐 View All (Login)":
    st.subheader("🔐 View All Letters (Protected)")
    pw = st.text_input("Enter Password", type="password")
    if pw == PASSWORD:
        st.success("Access granted.")
        all_letters = get_letters()
        for i, (_, feeling, msg, ts) in enumerate(all_letters):
            st.text_area(f"{feeling} — {ts}", value=msg, height=150, disabled=True, key=f"all_{i}")
    elif pw:
        st.error("Incorrect password.")

