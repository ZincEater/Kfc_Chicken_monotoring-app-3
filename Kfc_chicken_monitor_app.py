import streamlit as st
from datetime import datetime

st.set_page_config(page_title="KFC Shift Pro", layout="centered")

st.title("🍗 KFC Shift Manager")
st.subheader("Waste Reduction & Drop Tracker")

# 1. Current Stats
st.divider()
col1, col2 = st.columns(2)

with col1:
    on_hand = st.number_input("Current OR Pieces", min_value=0, step=1)
with col2:
    time_now = datetime.now().strftime("%H:%M")
    st.metric("Current Time", time_now)

# 2. Decision Logic (The "Should I Drop?" Engine)
st.header("Drop Recommendation")
target_pieces = 20 # You can adjust this based on your store's average late-night sales

if on_hand >= target_pieces:
    st.success("✅ DO NOT DROP. You have enough to cover the window.")
else:
    needed = target_pieces - on_hand
    st.warning(f"⚠️ LOW STOCK. You need approx {needed} more pieces.")
    st.info("Reminder: Minimum drop is 2-Head (18 pieces).")

# 3. Quick Log (Saves to a local CSV or just displays)
st.divider()
st.header("End of Night Log")
waste_count = st.number_input("Pieces Wasted at 9:00 PM", min_value=0, step=1)

if st.button("Log Shift Data"):
    # In a full app, you'd append this to a database or Google Sheet
    st.write(f"Logged: {datetime.now().date()} | Waste: {waste_count} pieces")
    if waste_count > 30:
        st.error("High Waste Alert: Adjust the 7:25 PM drop for this day next week!")
    else:
        st.balloons()
        st.success("Great shift! Efficiency is up.")

# 4. Peer-to-Peer "Friend" Mode
st.sidebar.markdown("### 📋 Supervisor Notes")
st.sidebar.info("If it's past 7:30 PM, the kitchen is CLOSED. Pivot customers to Burgers/Zingers.")
