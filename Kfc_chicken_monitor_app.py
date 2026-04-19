import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="KFC Waste Tracker Pro", layout="centered")

# --- EXCEL DATABASE LOGIC ---
EXCEL_FILE = 'kfc_weekly_data.xlsx'
GOAL_LIMIT = 24

def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    return pd.DataFrame(columns=['Date', 'Time', 'Cooked_Pieces', 'Wasted_Pieces'])

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)

# --- APP UI ---
st.title("🍗 KFC Efficiency Tracker")
st.markdown(f"**Target:** Keep nightly waste below **{GOAL_LIMIT} pieces**")

# --- 1. DATA ENTRY ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        date_entry = st.date_input("Shift Date", datetime.now())
        # Step=18 matches your 2-head minimum requirement
        cooked = st.number_input("Total Cooked (Pieces)", min_value=0, step=18) 
    with col2:
        time_entry = st.time_input("Log Time", datetime.now().time())
        wasted = st.number_input("Total Wasted (Pieces)", min_value=0, step=1)

    if st.button("💾 Log Shift to Excel", use_container_width=True):
        df = load_data()
        new_row = pd.DataFrame([{
            'Date': date_entry.strftime("%Y-%m-%d"),
            'Time': time_entry.strftime("%H:%M"),
            'Cooked_Pieces': cooked,
            'Wasted_Pieces': wasted
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        
        # Immediate Feedback
        if wasted <= GOAL_LIMIT:
            st.balloons()
            st.success(f"Nice work! Waste was {wasted}, which is under the {GOAL_LIMIT} goal.")
        else:
            st.error(f"Waste was {wasted}. That's {wasted - GOAL_LIMIT} over the limit. Check the 7:30pm drop next time.")

# --- 2. THE CHART WITH GOAL LINE ---
st.divider()
st.subheader("📊 Weekly Performance vs Goal")

df_display = load_data()

if not df_display.empty:
    # Prepare data for the chart
    chart_data = df_display.groupby('Date')[['Wasted_Pieces']].sum().reset_index()
    chart_data['Goal'] = GOAL_LIMIT # Adds the flat 24-piece line
    
    # Using Streamlit's line chart
    # It will show 'Wasted_Pieces' and a flat 'Goal' line at 24
    st.line_chart(chart_data.set_index('Date'))
    
    # Show history for easy adjustments
    st.subheader("📝 Edit Excel Records")
    edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True)
    
    if st.button("Confirm Changes"):
        save_data(edited_df)
        st.toast("Excel file updated!")
else:
    st.info("No data in the Excel log yet.")

# --- 3. DOWNLOAD FOR RGM ---
if not df_display.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="Excel 📥 Download for RGM",
            data=f,
            file_name=f"KFC_Waste_Report_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
