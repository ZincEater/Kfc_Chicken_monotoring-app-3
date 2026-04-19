import streamlit as st
import pandas as pd
import os
from datetime import datetime, time

st.set_page_config(page_title="KFC Drop Monitor", layout="wide")

# --- SETTINGS ---
EXCEL_FILE = 'kfc_master_waste_log.xlsx'
GOAL_LIMIT = 24
PRODUCTS = ['Original Recipe', 'Wicked Wings', 'Boneless', 'Original Filets', 'Zingers', 'Tenders']
CREW_MEMBERS = ['Memphis', 'Anandu', 'Levi', 'Jazz'] 

# Specific cooking increments provided by you
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
        st.error(f"Error loading Excel: {e}")
        return pd.DataFrame()

def save_data(df):
    try:
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Error saving to Excel: {e}")

# --- APP UI ---
st.title("🍗 KFC Unit-Drop & Waste Monitor")

# --- SIDEBAR ADMIN ---
st.sidebar.header("⚙️ Admin Settings")
confirm_clear = st.sidebar.checkbox("I want to PERMANENTLY clear all shift data")
if confirm_clear:
    if st.sidebar.button("🚨 WIPE ALL DATA"):
        empty_df = load_data().iloc[0:0]
        save_data(empty_df)
        st.sidebar.success("Log cleared! Refreshing...")
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
        comment = st.text_area("Shift Comments", placeholder="Notes about the shift...")

    st.divider()
    st.write("**Enter Shift Totals (Increments set to store standards):**")
    cooked_inputs = {}
    waste_inputs = {}
    
    for product in PRODUCTS:
        row_col1, row_col2, row_col3 = st.columns([2, 1, 1])
        with row_col1:
            # Display the increment rule next to the name for the crew
            step = PRODUCT_STEPS.get(product, 1)
            st.write(f"### {product}")
            st.caption(f"Cooked in batches of {step}")
            
        with row_col2:
            cooked_inputs[product] = st.number_input(f"Total Cooked", min_value=0, step=step, key=f"c_{product}")
        with row_col3:
            waste_inputs[product] = st.number_input(f"Total Waste", min_value=0, step=1, key=f"w_{product}")

    if st.button("💾 Save Full Shift Log", use_container_width=True):
        df = load_data()
        total_waste = sum(waste_inputs.values())
        
        new_entry = {
            'Date': date_entry.strftime("%Y-%m-%d"),
            'Week_Number': week_num,
            'Time': log_time.strftime("%H:%M"),
            'Cook_Name': cook_name,
            'Comments': comment
        }
        for p in PRODUCTS:
            new_entry[f'{p}_Cooked'] = cooked_inputs[p]
            new_entry[f'{p}_Waste'] = waste_inputs[p]
            
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success(f"Shift logged! Total Waste: {total_waste} pieces.")

# --- 2. ANALYTICS ---
st.divider()
df_display = load_data()

if not df_display.empty:
    waste_cols = [f'{p}_Waste' for p in PRODUCTS]
    cooked_cols = [f'{p}_Cooked' for p in PRODUCTS]
    df_display['Total_Waste'] = df_display[waste_cols].sum(axis=1)

    tab1, tab2, tab3 = st.tabs(["📉 Yield Graphs", "🏆 Cook Leaderboard", "🗄️ Master Data"])

    with tab1:
        st.subheader("Daily Waste vs Goal")
        line_data = df_display.groupby('Date')['Total_Waste'].sum().reset_index()
        line_data['Goal'] = GOAL_LIMIT
        st.line_chart(line_data.set_index('Date'))
        
        st.subheader("Waste Percentage by Product")
        avg_cooked = df_display[cooked_cols].sum()
        avg_waste = df_display[waste_cols].sum()
        
        # Calculate yield while ignoring zero-cook items to prevent errors
        yield_results = []
        for p in PRODUCTS:
            c = avg_cooked[f'{p}_Cooked']
            w = avg_waste[f'{p}_Waste']
            yield_results.append((w / c * 100) if c > 0 else 0)
            
        yield_df = pd.DataFrame(yield_results, index=PRODUCTS, columns=['Waste %'])
        st.bar_chart(yield_df)

    with tab2:
        st.subheader("Average Waste per Cook")
        cook_stats = df_display.groupby('Cook_Name')['Total_Waste'].mean().sort_values()
        st.bar_chart(cook_stats)

    with tab3:
        st.subheader("Master Excel Records")
        st.data_editor(df_display, num_rows="dynamic", use_container_width=True)

# --- 3. DOWNLOAD ---
if not df_display.empty:
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Detailed Excel",
            data=f,
            file_name=f"KFC_Master_Log_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
