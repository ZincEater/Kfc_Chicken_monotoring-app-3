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
with st.expander("📝 Log Shift Details (Adjustable Time)", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        # Now fully adjustable for back-logging
        date_entry = st.date_input("Shift Date", datetime.now())
        cook_name = st.selectbox("Who was the Cook?", CREW_MEMBERS)
        week_num = date_entry.isocalendar()[1]
    with col_b:
        # Time picker now defaults to now, but you can change it to 9:00 PM manually
        log_time = st.time_input("Time of Final Count", datetime.now().time())
        total_cooked = st.number_input("Total OR Pieces Cooked", min_value=0, step=18)
    with col_c:
        comment = st.text_area("Shift Comments", placeholder="e.g. Rush at 8:30, rain, etc.")

    st.write("---")
    st.write("**Waste Counts (Enter pieces found at close):**")
    p_cols = st.columns(3)
    waste_inputs = {}
    for i, product in enumerate(PRODUCTS):
        with p_cols[i % 3]:
            waste_inputs[product] = st.number_input(f"{product}", min_value=0, step=1, key=f"inp_{product}")

    if st.button("💾 Save Shift Data", use_container_width=True):
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
            st.success(f"Log Saved for {log_time.strftime('%H:%M')}! Total Waste: {total_this_shift}")
        else:
            st.warning(f"Log Saved! Waste was {total_this_shift}. ({total_this_shift - GOAL_LIMIT} over goal)")

# --- 2. GRAPHS & LEADERBOARD ---
st.divider()
df_display = load_data()

if not df_display.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    df_display['Total_Waste'] = df_display[waste_cols].sum(axis=1)

    tab1, tab2, tab3 = st.tabs(["📉 Efficiency Graphs", "🏆 Cook Leaderboard", "🗄️ Master Data"])

    with tab1:
        st.subheader("Daily Waste Trend")
        line_data = df_display.groupby('Date')['Total_Waste'].sum().reset_index()
        line_data['Goal'] = GOAL_LIMIT
        st.line_chart(line_data.set_index('Date'))
        
        st.subheader("Product Breakdown")
        product_totals = df_display[waste_cols].sum()
        product_totals.index = [p.replace('_Waste', '') for p in product_totals.index]
        st.bar_chart(product_totals)

    with tab2:
        st.subheader("Average Waste per Cook")
        cook_stats = df_display.groupby('Cook_Name')['Total_Waste'].mean().sort_values()
        st.bar_chart(cook_stats)

    with tab3:
        st.subheader("Edit/Review Records")
        # Added a filter by date so you can find old shifts easily
        st.data_editor(df_display, num_rows="dynamic", use_container_width=True)

# --- 3. DOWNLOAD ---
if not df_display.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Excel Report",
            data=f,
            file_name=f"KFC_Waste_Report_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
