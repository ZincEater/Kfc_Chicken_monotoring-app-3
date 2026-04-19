import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="KFC Multi-Product Tracker", layout="wide")

# --- EXCEL DATABASE LOGIC ---
EXCEL_FILE = 'kfc_inventory_waste.xlsx'
GOAL_LIMIT = 24
PRODUCTS = [
    'Original Recipe', 'Wicked Wings', 'Boneless', 
    'Original Filets', 'Zingers', 'Tenders'
]

def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    # Create columns for Date, Time, and then a Waste column for every product
    cols = ['Date', 'Time', 'Total_Cooked'] + [f'{p}_Waste' for p in PRODUCTS]
    return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)

# --- APP UI ---
st.title("🍗 KFC Full Product Waste Monitor")
st.markdown(f"**Nightly Goal:** Keep total binned pieces under **{GOAL_LIMIT}**")

# --- 1. DATA ENTRY ---
with st.expander("📝 Log End-of-Shift Waste", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        date_entry = st.date_input("Shift Date", datetime.now())
        total_cooked = st.number_input("Total OR Pieces Cooked (Drops)", min_value=0, step=18)
    with col_b:
        log_time = st.time_input("Log Time", datetime.now().time())

    st.write("---")
    st.write("**Enter Waste Counts per Product:**")
    
    # Create a grid for product inputs
    p_cols = st.columns(3)
    waste_inputs = {}
    
    for i, product in enumerate(PRODUCTS):
        with p_cols[i % 3]:
            waste_inputs[product] = st.number_input(f"{product}", min_value=0, step=1, key=product)

    if st.button("💾 Save to Weekly Excel", use_container_width=True):
        df = load_data()
        
        # Calculate total waste for this entry
        total_this_shift = sum(waste_inputs.values())
        
        new_data = {
            'Date': date_entry.strftime("%Y-%m-%d"),
            'Time': log_time.strftime("%H:%M"),
            'Total_Cooked': total_cooked
        }
        # Add the specific product waste
        for p in PRODUCTS:
            new_data[f'{p}_Waste'] = waste_inputs[p]
            
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        save_data(df)
        
        # Feedback logic
        if total_this_shift <= GOAL_LIMIT:
            st.balloons()
            st.success(f"Success! Total waste was {total_this_shift}. Under the {GOAL_LIMIT} limit.")
        else:
            st.error(f"Total waste: {total_this_shift}. You are {total_this_shift - GOAL_LIMIT} pieces over goal.")

# --- 2. THE ANALYTICS ---
st.divider()
df_display = load_data()

if not df_display.empty:
    # 2.1 Performance Chart
    st.subheader("📊 Waste Trends by Product")
    
    # Prepare chart data (Sum of waste across all product columns)
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    chart_data = df_display.groupby('Date')[waste_cols].sum()
    
    # Total Waste vs Goal Line
    total_daily_waste = chart_data.sum(axis=1).to_frame(name='Total_Waste')
    total_daily_waste['Goal'] = GOAL_LIMIT
    
    tab1, tab2 = st.tabs(["Total Waste vs Goal", "Breakdown by Product"])
    
    with tab1:
        st.line_chart(total_daily_waste)
    
    with tab2:
        st.bar_chart(chart_data)

    # 2.2 Success Rate
    success_count = (df_display[waste_cols].sum(axis=1) <= GOAL_LIMIT).sum()
    total_shifts = len(df_display)
    st.metric("Weekly Success Rate", f"{success_count} / {total_shifts} Shifts", 
              delta=f"{int((success_count/total_shifts)*100)}%" if total_shifts > 0 else None)

    # 2.3 Raw Data Table
    st.subheader("📝 Edit Excel Records")
    edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True)
    if st.button("Confirm Adjustments"):
        save_data(edited_df)
        st.toast("Excel updated!")

# --- 3. DOWNLOAD ---
if not df_display.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Excel for RGM",
            data=f,
            file_name=f"KFC_Full_Waste_Report_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
