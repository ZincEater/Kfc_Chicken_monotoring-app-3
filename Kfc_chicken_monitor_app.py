import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="KFC Shift Monitor", layout="centered")

# --- DATABASE LOGIC ---
# This keeps your data alive during the session
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'On_Hand', 'Action'])

st.title("🍗 KFC Shift Monitor")
st.markdown("### Manage Chicken & Edit History")

# --- 1. ENTRY SECTION ---
with st.container():
    st.subheader("Current Status")
    col1, col2 = st.columns(2)
    
    with col1:
        current_count = st.number_input("How many OR pieces now?", min_value=0, step=1)
    with col2:
        # Defaults to current time, but you can adjust it if you're logging late
        entry_time = st.time_input("Log Time", datetime.now().time())

    if st.button("➕ Add Entry", use_container_width=True):
        new_entry = {
            'Time': entry_time.strftime("%H:%M"),
            'On_Hand': current_count,
            'Action': "Checked"
        }
        # Add new data to the session state
        st.session_state.history = pd.concat([
            st.session_state.history, 
            pd.DataFrame([new_entry])
        ], ignore_index=True)
        st.success(f"Logged {current_count} pieces for {entry_time.strftime('%H:%M')}")

# --- 2. EDIT / ADJUST HISTORY ---
st.divider()
st.subheader("📊 Shift History & Adjustments")

if not st.session_state.history.empty:
    # We use st.data_editor to let you change numbers directly in the table!
    edited_df = st.data_editor(
        st.session_state.history,
        num_rows="dynamic", # This allows you to delete rows by selecting them
        use_container_width=True,
        key="history_editor"
    )
    
    # Update the master history if you changed something in the table
    st.session_state.history = edited_df

    st.info("💡 You can click any cell above to change the time or count. Use the checkbox on the left to delete a row.")
else:
    st.write("No data logged for this shift yet.")

# --- 3. RECAP FOR RGM ---
if st.sidebar.button("🗑️ Clear Shift (New Day)"):
    st.session_state.history = pd.DataFrame(columns=['Time', 'On_Hand', 'Action'])
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write(f"**Supervisor:** You")
st.sidebar.write("**Store Status:** Kitchen Closes @ 7:30 PM")
