import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="KFC Crew Efficiency", layout="wide")

# --- SETTINGS ---
EXCEL_FILE = 'kfc_master_waste_log.xlsx'
GOAL_LIMIT = 24
PRODUCTS = ['Original Recipe', 'Wicked Wings', 'Boneless', 'Original Filets', 'Zingers', 'Tenders']
CREW_MEMBERS = ['Memphis', 'Anandu', 'Levi', 'Jazz'] 

def load_data():
    try:
        if os.path.exists(EXCEL_FILE):
            return pd.read_excel(EXCEL_FILE, engine='openpyxl')
        cols = ['Date', 'Week_Number', 'Time', 'Cook_Name', 'Total_Cooked_OR'] + \
               [f'{p}_Waste' for p in PRODUCTS] + ['Comments']
        return pd.DataFrame(columns=cols)
    except Exception as e:
        st.error(f"Error loading Excel: {e}")
        return pd.DataFrame()

def save_data(df):
    try:
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Error saving to Excel: {e}")

# --- APP UI ---
st.title("🍗 KFC Crew & Waste Monitor")
st.markdown(f"**Nightly Target:** Keep shift waste under **{GOAL_LIMIT} pieces** total.")

# --- 1. DATA ENTRY ---
with st.expander("📝 Log End-of-Shift Details", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        date_entry = st.date_input("Shift Date", datetime.now())
        cook_name = st.selectbox("Who was the Cook?", CREW_MEMBERS)
        week_num = date_entry.isocalendar()[1]
    with col_b:
        log_time = st.time_input("Log Time", datetime.now().time())
        total_cooked = st.number_input("Total OR Pieces Cooked", min_value=0, step=18)
    with col_c:
        comment = st.text_area("Shift Comments", placeholder="e.g. Sudden bus, raining, etc.")

    st.write("---")
    st.write("**Waste Counts (Pieces):**")
    p_cols = st.columns(3)
    waste_inputs = {}
    for i, product in enumerate(PRODUCTS):
        with p_cols[i % 3]:
            waste_inputs[product] = st.number_input(f"{product}", min_value=0, step=1, key=f"input_{product}")

    if st.button("💾 Save Shift to Master Log", use_container_width=True):
        df = load_data()
        total_this_shift = sum(waste_inputs.values())
        
        new_entry = {
            'Date': date_entry.strftime("%Y-%m-%d"),
            'Week_Number': week_num,
            'Time': log_time.strftime("%H:%M"),
            'Cook_Name': cook_name,
            'Total_Cooked_OR': total_cooked,
            'Comments': comment
        }
        for p in PRODUCTS:
            new_entry[f'{p}_Waste'] = waste_inputs[p]
            
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        
        if total_this_shift <= GOAL_LIMIT:
            st.balloons()
            st.success(f"Nice work, {cook_name}! Only {total_this_shift} pieces wasted.")
        else:
            st.warning(f"Total waste: {total_this_shift}. Let's watch the 7:30pm drop tomorrow.")

# --- 2. GRAPHS & LEADERBOARD ---
st.divider()
df_display = load_data()

if not df_display.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    df_display['Total_Waste'] = df_display[waste_cols].sum(axis=1)

    # Analytics Tabs
    tab1, tab2, tab3 = st.tabs(["📉 Efficiency Graphs", "🏆 Cook Leaderboard", "🗄️ Master Data"])

    with tab1:
        st.subheader("Daily Waste vs. 24-Piece Goal")
        line_data = df_display.groupby('Date')['Total_Waste'].sum().reset_index()
        line_data['Goal'] = GOAL_LIMIT
        st.line_chart(line_data.set_index('Date'))
        
        st.subheader("Product Waste Breakdown")
        product_totals = df_display[waste_cols].sum()
        product_totals.index = [p.replace('_Waste', '') for p in product_totals.index]
        st.bar_chart(product_totals)

    with tab2:
        st.subheader("Average Waste per Cook")
        cook_stats = df_display.groupby('Cook_Name')['Total_Waste'].mean().sort_values()
        st.bar_chart(cook_stats)
        st.info("The shorter the bar, the more efficient the cook.")

    with tab3:
        st.subheader("All Shift Records")
        st.data_editor(df_display, num_rows="dynamic", use_container_width=True)

# --- 3. DOWNLOAD FOR RGM ---
if not df_display.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Excel for RGM",
            data=f,
            file_name=f"KFC_Master_Log_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
