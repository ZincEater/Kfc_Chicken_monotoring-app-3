import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="KFC Crew Efficiency", layout="wide")

# --- SETTINGS ---
EXCEL_FILE = 'kfc_crew_waste_log.xlsx'
GOAL_LIMIT = 24
PRODUCTS = ['Original Recipe', 'Wicked Wings', 'Boneless', 'Original Filets', 'Zingers', 'Tenders']
# You can update this list with your actual crew names
CREW_MEMBERS = ['Self', 'Cook A', 'Cook B', 'Cook C'] 

def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    cols = ['Date', 'Time', 'Cook_Name', 'Total_Cooked_OR'] + [f'{p}_Waste' for p in PRODUCTS]
    return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)

# --- APP UI ---
st.title("🍗 KFC Crew & Waste Monitor")
st.markdown(f"**Target:** Shift waste under **{GOAL_LIMIT} pieces** total.")

# --- 1. DATA ENTRY ---
with st.expander("📝 Log Shift Details", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        date_entry = st.date_input("Shift Date", datetime.now())
        cook_name = st.selectbox("Who was the Cook?", CREW_MEMBERS)
    with col_b:
        log_time = st.time_input("Log Time", datetime.now().time())
    with col_c:
        total_cooked = st.number_input("Total OR Pieces Cooked", min_value=0, step=18)

    st.write("---")
    st.write("**Waste Counts:**")
    p_cols = st.columns(3)
    waste_inputs = {}
    for i, product in enumerate(PRODUCTS):
        with p_cols[i % 3]:
            waste_inputs[product] = st.number_input(f"{product}", min_value=0, step=1, key=product)

    if st.button("💾 Save to Crew Log", use_container_width=True):
        df = load_data()
        total_this_shift = sum(waste_inputs.values())
        
        new_entry = {
            'Date': date_entry.strftime("%Y-%m-%d"),
            'Time': log_time.strftime("%H:%M"),
            'Cook_Name': cook_name,
            'Total_Cooked_OR': total_cooked
        }
        for p in PRODUCTS:
            new_entry[f'{p}_Waste'] = waste_inputs[p]
            
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        
        if total_this_shift <= GOAL_LIMIT:
            st.balloons()
            st.success(f"Top work, {cook_name}! Only {total_this_shift} pieces wasted.")
        else:
            st.error(f"Waste was {total_this_shift}. Let's try to lower the 7:30 drop tomorrow.")

# --- 2. THE LEADERBOARD & ANALYTICS ---
st.divider()
df_display = load_data()

if not df_display.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    df_display['Total_Waste'] = df_display[waste_cols].sum(axis=1)

    tab1, tab2, tab3 = st.tabs(["Leaderboard", "Product Breakdown", "History"])

    with tab1:
        st.subheader("🏆 Cook Efficiency (Avg Waste per Shift)")
        leaderboard = df_display.groupby('Cook_Name')['Total_Waste'].mean().sort_values()
        st.bar_chart(leaderboard)
        st.info("The shorter the bar, the better the cook managed their drops!")

    with tab2:
        st.subheader("📦 Most Wasted Products")
        product_totals = df_display[waste_cols].sum().sort_values(ascending=False)
        st.bar_chart(product_totals)

    with tab3:
        st.subheader("📝 Edit Shift Records")
        edited_df = st.data_editor(df_display.drop(columns=['Total_Waste']), num_rows="dynamic")
        if st.button("Confirm Changes"):
            save_data(edited_df)
            st.rerun()

# --- 3. DOWNLOAD ---
if not df_display.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Detailed Excel",
            data=f,
            file_name=f"KFC_Detailed_Report_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
