import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="KFC Master Waste Log", layout="wide")

# --- SETTINGS ---
EXCEL_FILE = 'kfc_master_waste_log.xlsx'
GOAL_LIMIT = 24
PRODUCTS = ['Original Recipe', 'Wicked Wings', 'Boneless', 'Original Filets', 'Zingers', 'Tenders']
CREW_MEMBERS = ['Self', 'Cook A', 'Cook B', 'Cook C'] 

def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    # New column 'Week_Number' added for tracking
    cols = ['Date', 'Week_Number', 'Time', 'Cook_Name', 'Total_Cooked_OR'] + \
           [f'{p}_Waste' for p in PRODUCTS] + ['Comments']
    return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)

# --- APP UI ---
st.title("🍗 KFC Master Efficiency Log")
st.markdown("Track waste across multiple weeks and monitor long-term trends.")

# --- 1. DATA ENTRY ---
with st.expander("📝 Log New Shift", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        date_val = st.date_input("Shift Date", datetime.now())
        cook_name = st.selectbox("Cook Name", CREW_MEMBERS)
        # Automatic week number calculation
        week_num = date_val.isocalendar()[1]
    with col_b:
        log_time = st.time_input("Log Time", datetime.now().time())
        total_cooked = st.number_input("Total OR Pieces Cooked", min_value=0, step=18)
    with col_c:
        st.info(f"Entry for **Week {week_num}**")
        comment = st.text_area("Shift Comments", placeholder="e.g. Sudden bus, rain, local rugby game...")

    st.write("---")
    st.write("**Waste Counts:**")
    p_cols = st.columns(3)
    waste_inputs = {}
    for i, product in enumerate(PRODUCTS):
        with p_cols[i % 3]:
            waste_inputs[product] = st.number_input(f"{product}", min_value=0, step=1, key=product)

    if st.button("💾 Append to Master Log", use_container_width=True):
        df = load_data()
        total_this_shift = sum(waste_inputs.values())
        
        new_entry = {
            'Date': date_val.strftime("%Y-%m-%d"),
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
        st.success(f"Shift logged successfully! Total waste: {total_this_shift}")

# --- 2. MULTI-WEEK ANALYTICS ---
st.divider()
df_master = load_data()

if not df_master.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    df_master['Total_Waste'] = df_master[waste_cols].sum(axis=1)

    tab1, tab2, tab3 = st.tabs(["Weekly Trends", "Cook Leaderboard", "Master Data"])

    with tab1:
        st.subheader("📈 Long-Term Waste Trends")
        # Group by week to see if we are getting better over time
        weekly_stats = df_master.groupby('Week_Number')['Total_Waste'].mean()
        st.line_chart(weekly_stats)
        st.write("This shows the average waste per shift for each week.")

    with tab2:
        st.subheader("🏆 Efficiency by Cook")
        cook_stats = df_master.groupby('Cook_Name')['Total_Waste'].mean().sort_values()
        st.bar_chart(cook_stats)

    with tab3:
        st.subheader("🗄️ All Records")
        # Filter by week if needed
        weeks_available = sorted(df_master['Week_Number'].unique(), reverse=True)
        selected_week = st.multiselect("Filter by Week", weeks_available, default=weeks_available)
        
        display_df = df_master[df_master['Week_Number'].isin(selected_week)]
        st.data_editor(display_df, use_container_width=True)

# --- 3. DOWNLOAD ---
if not df_master.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Master Excel",
            data=f,
            file_name=f"KFC_Master_Log_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
