import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="KFC Master Log & Analytics", layout="wide")

# --- SETTINGS ---
EXCEL_FILE = 'kfc_master_waste_log.xlsx'
GOAL_LIMIT = 24
PRODUCTS = ['Original Recipe', 'Wicked Wings', 'Boneless', 'Original Filets', 'Zingers', 'Tenders']
CREW_MEMBERS = ['Self', 'Cook A', 'Cook B', 'Cook C'] 

def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    cols = ['Date', 'Week_Number', 'Time', 'Cook_Name', 'Total_Cooked_OR'] + \
           [f'{p}_Waste' for p in PRODUCTS] + ['Comments']
    return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)

# --- APP UI ---
st.title("🍗 KFC Master Efficiency & Analytics")

# --- 1. DATA ENTRY ---
with st.expander("📝 Log End-of-Shift Data", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        date_val = st.date_input("Shift Date", datetime.now())
        cook_name = st.selectbox("Cook Name", CREW_MEMBERS)
        week_num = date_val.isocalendar()[1]
    with col_b:
        log_time = st.time_input("Log Time", datetime.now().time())
        total_cooked = st.number_input("Total OR Pieces Cooked", min_value=0, step=18)
    with col_c:
        comment = st.text_area("Shift Comments (Optional)", placeholder="e.g. Bus arrival, weather, equipment issues...")

    st.write("---")
    st.write("**Waste Counts (Pieces):**")
    p_cols = st.columns(3)
    waste_inputs = {}
    for i, product in enumerate(PRODUCTS):
        with p_cols[i % 3]:
            waste_inputs[product] = st.number_input(f"{product}", min_value=0, step=1, key=product)

    if st.button("💾 Save Shift Data", use_container_width=True):
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
        
        if total_this_shift <= GOAL_LIMIT:
            st.balloons()
            st.success(f"Shift Logged! Total Waste: {total_this_shift} (Under Goal)")
        else:
            st.warning(f"Shift Logged! Total Waste: {total_this_shift} (Over Goal by {total_this_shift - GOAL_LIMIT})")

# --- 2. THE GRAPHS & ANALYTICS ---
st.divider()
df_master = load_data()

if not df_master.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    df_master['Total_Waste'] = df_master[waste_cols].sum(axis=1)

    # Analytics Tabs
    tab1, tab2, tab3 = st.tabs(["📉 Waste Graphs", "🏆 Cook Leaderboard", "🗄️ Master Table"])

    with tab1:
        st.subheader("Daily Waste vs. 24-Piece Goal")
        # Prepare data for line chart
        line_data = df_master.groupby('Date')['Total_Waste'].sum().reset_index()
        line_data['Goal'] = GOAL_LIMIT
        st.line_chart(line_data.set_index('Date'))
        
        st.subheader("Product Waste Breakdown")
        product_totals = df_master[waste_cols].sum()
        # Clean up labels for the bar chart
        product_totals.index = [p.replace('_Waste', '') for p in product_totals.index]
        st.bar_chart(product_totals)

    with tab2:
        st.subheader("Average Waste per Cook")
        cook_stats = df_master.groupby('Cook_Name')['Total_Waste'].mean().sort_values()
        st.bar_chart(cook_stats)
        st.caption("Lower is better: Represents the average amount binned on their shifts.")

    with tab3:
        st.subheader("All Logged Records")
        st.data_editor(df_master, use_container_width=True, num_rows="dynamic")

# --- 3. EXCEL DOWNLOAD ---
if not df_master.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Master Excel",
            data=f,
            file_name=f"KFC_Master_Log_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
