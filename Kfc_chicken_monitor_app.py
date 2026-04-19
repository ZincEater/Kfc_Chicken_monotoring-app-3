import streamlit as st
import pandas as pd
import os
from datetime import datetime, time

st.set_page_config(page_title="KFC Yield Master", layout="wide")

# --- SETTINGS ---
EXCEL_FILE = 'kfc_master_waste_log.xlsx'
GOAL_LIMIT = 24
PRODUCTS = ['Original Recipe', 'Wicked Wings', 'Boneless', 'Original Filets', 'Zingers', 'Tenders']
CREW_MEMBERS = ['Memphis', 'Anandu', 'Levi', 'Jazz'] 

PRODUCT_STEPS = {
    'Original Recipe': 18,
    'Wicked Wings': 20,
    'Boneless': 20,
    'Original Filets': 5,
    'Zingers': 5,
    'Tenders': 10
}

def load_data():
    try:
        if os.path.exists(EXCEL_FILE):
            return pd.read_excel(EXCEL_FILE, engine='openpyxl')
        cols = ['Date', 'Week_Number', 'Time', 'Cook_Name'] + \
               [f'{p}_Cooked' for p in PRODUCTS] + \
               [f'{p}_Waste' for p in PRODUCTS] + ['Comments']
        return pd.DataFrame(columns=cols)
    except Exception as e:
        return pd.DataFrame() # Return empty if error

def save_data(df):
    try:
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Error saving: {e}")

# --- APP UI ---
st.title("🍗 KFC Full Yield & Waste Monitor")

# Load data at start
df_master = load_data()

# --- SIDEBAR ---
st.sidebar.header("📊 Admin")
# Always show download if the file exists (even if empty, it downloads the template)
if os.path.exists(EXCEL_FILE):
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button("📥 Export to Excel", f, "KFC_Report.xlsx", use_container_width=True)

st.sidebar.divider()
confirm_clear = st.sidebar.checkbox("Permit data wipe")
if confirm_clear:
    if st.sidebar.button("🚨 WIPE ALL DATA"):
        empty_df = load_data().iloc[0:0]
        save_data(empty_df)
        st.rerun()

# --- 1. DATA ENTRY ---
with st.expander("📝 Log Shift Details", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        date_entry = st.date_input("Shift Date", datetime.now())
        cook_name = st.selectbox("Who was the Cook?", CREW_MEMBERS)
        week_num = date_entry.isocalendar()[1]
    with col_b:
        log_time = st.time_input("Time of Final Count", value=time(21, 0))
    with col_c:
        comment = st.text_area("Shift Comments", placeholder="Bus arrival, rain, events, etc.")

    st.divider()
    cooked_inputs = {}
    waste_inputs = {}
    
    for product in PRODUCTS:
        r1, r2, r3 = st.columns([2, 1, 1])
        step = PRODUCT_STEPS.get(product, 1)
        r1.write(f"### {product}")
        cooked_inputs[product] = r2.number_input("Cooked", 0, step=step, key=f"c_{product}")
        waste_inputs[product] = r3.number_input("Waste", 0, step=1, key=f"w_{product}")

    if st.button("💾 Save Shift Data", use_container_width=True):
        new_row = {
            'Date': date_entry.strftime("%Y-%m-%d"),
            'Week_Number': week_num,
            'Time': log_time.strftime("%H:%M"),
            'Cook_Name': cook_name,
            'Comments': comment
        }
        for p in PRODUCTS:
            new_row[f'{p}_Cooked'] = cooked_inputs[p]
            new_row[f'{p}_Waste'] = waste_inputs[p]
        
        df_updated = pd.concat([df_master, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df_updated)
        st.success("Shift logged! Refreshing analytics...")
        st.rerun()

# --- 2. ANALYTICS ---
st.divider()

if not df_master.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    cooked_cols = [f'{p}_Cooked' for p in PRODUCTS]
    df_master['Total_Waste'] = df_master[waste_cols].sum(axis=1)

    tab1, tab2, tab3 = st.tabs(["📉 Yield Graphs", "🏆 Leaderboard", "🗄️ Master Table"])

    with tab1:
        line_data = df_master.groupby('Date')['Total_Waste'].sum().reset_index()
        line_data['Goal'] = GOAL_LIMIT
        st.line_chart(line_data.set_index('Date'))
        
        # Product Bar Chart
        avg_w = df_master[waste_cols].sum()
        avg_w.index = PRODUCTS
        st.bar_chart(avg_w)

    with tab2:
        st.bar_chart(df_master.groupby('Cook_Name')['Total_Waste'].mean())

    with tab3:
        st.data_editor(df_master, use_container_width=True, num_rows="dynamic")
else:
    st.info("No data logged yet. Once you save your first shift, graphs will appear here!")
    st.subheader("Current Master Sheet (Empty)")
    st.data_editor(df_master, use_container_width=True)
