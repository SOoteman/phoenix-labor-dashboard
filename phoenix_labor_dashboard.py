#!/usr/bin/env python3
"""
Phoenix Labor Cost Dashboard - Streamlit App (Clean Version)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests
import os

st.set_page_config(
    page_title="Phoenix Labor Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== HELPER FUNCTIONS ====================

@st.cache_data(ttl=3600)
def get_live_eur_usd():
    try:
        url = "https://api.frankfurter.app/latest?from=EUR&to=USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return round(response.json()['rates']['USD'], 4)
    except:
        pass
    return 1.085

def get_xcg_usd():
    return 0.558

def load_data():
    """Load data from the clean Excel file"""
    excel_path = "Phoenix_Labor_Cost_Tracker_Clean.xlsx"
    
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path, sheet_name="Labor_Data_Entry")
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
            return pd.DataFrame()
    else:
        st.warning("Excel file not found in repository. Please upload it below.")
        uploaded_file = st.file_uploader(
            "Upload your Phoenix Labor Cost Tracker Clean Excel file",
            type=["xlsx"],
            key="excel_uploader"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file, sheet_name="Labor_Data_Entry")
            except Exception as e:
                st.error(f"Error reading uploaded file: {e}")
                return pd.DataFrame()
        else:
            st.info("Please upload the Excel file to see the dashboard.")
            return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]
    
    # Calculate Total Hours
    df['Total Hours'] = (
        df.get('Regular Hours', 0) + 
        df.get('OT Hours 25%', 0) + 
        df.get('OT Hours 50%', 0)
    )
    
    # Filter Production Only
    if 'Production_Only (Yes/No)' in df.columns:
        df = df[df['Production_Only (Yes/No)'] == 'Yes'].copy()
    
    return df

def calculate_monthly_summary(df):
    if df.empty:
        return pd.DataFrame()
    
    summary = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
        'Total Hours': 'sum',
        'Total Cost (USD)': 'sum'
    }).reset_index()
    
    pivot = summary.pivot(index='Month (YYYY-MM)', columns='Entity', values=['Total Hours', 'Total Cost (USD)'])
    pivot.columns = [f"{col[0]} - {col[1]}" for col in pivot.columns]
    pivot = pivot.reset_index()
    
    if 'Total Hours - French - Saint Martin' in pivot.columns and 'Total Cost (USD) - French - Saint Martin' in pivot.columns:
        pivot['French Avg $/hr'] = pivot['Total Cost (USD) - French - Saint Martin'] / pivot['Total Hours - French - Saint Martin']
    
    if 'Total Hours - Dutch - Sint Maarten' in pivot.columns and 'Total Cost (USD) - Dutch - Sint Maarten' in pivot.columns:
        pivot['Dutch Avg $/hr'] = pivot['Total Cost (USD) - Dutch - Sint Maarten'] / pivot['Total Hours - Dutch - Sint Maarten']
    
    return pivot.sort_values('Month (YYYY-MM)')

# ==================== LOAD DATA ====================

df = load_data()
eur_usd = get_live_eur_usd()
xcg_usd = get_xcg_usd()

# ==================== SIDEBAR ====================

st.sidebar.header("⚙️ Settings")
st.sidebar.metric("EUR → USD (Live)", f"${eur_usd}")
st.sidebar.metric("XCG → USD (Peg)", f"${xcg_usd}")
st.sidebar.markdown("---")
st.sidebar.info("Rates are automatically updated. XCG is pegged to USD.")

# ==================== MAIN PAGE ====================

st.title("🏗️ Phoenix Labor Cost Dashboard")
st.markdown("**Production Staff Only** — Management & Owners excluded")

if df.empty:
    st.warning("No data loaded. Please make sure the Excel file is in the same folder.")
    st.stop()

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

total_hours = df['Total Hours'].sum() if 'Total Hours' in df.columns else 0
total_cost = df['Total Cost (USD)'].sum() if 'Total Cost (USD)' in df.columns else 0
avg_hourly = total_cost / total_hours if total_hours > 0 else 0

col1.metric("Total Production Hours", f"{total_hours:,.0f}")
col2.metric("Total Labor Cost (USD)", f"${total_cost:,.0f}")
col3.metric("Overall Avg Cost/Hour", f"${avg_hourly:.2f}")
col4.metric("Months of Data", df['Month (YYYY-MM)'].nunique() if 'Month (YYYY-MM)' in df.columns else 0)

st.markdown("---")

# Monthly Comparison
st.subheader("📊 Monthly French vs Dutch Comparison (Production Staff Only)")

monthly_summary = calculate_monthly_summary(df)

if not monthly_summary.empty:
    cols_to_show = ['Month (YYYY-MM)']
    if 'Total Hours - French - Saint Martin' in monthly_summary.columns:
        cols_to_show.extend(['Total Hours - French - Saint Martin', 'Total Cost (USD) - French - Saint Martin', 'French Avg $/hr'])
    if 'Total Hours - Dutch - Sint Maarten' in monthly_summary.columns:
        cols_to_show.extend(['Total Hours - Dutch - Sint Maarten', 'Total Cost (USD) - Dutch - Sint Maarten', 'Dutch Avg $/hr'])
    
    available_cols = [c for c in cols_to_show if c in monthly_summary.columns]
    st.dataframe(
        monthly_summary[available_cols].style.format({
            'French Avg $/hr': '${:.2f}',
            'Dutch Avg $/hr': '${:.2f}',
            'Total Cost (USD) - French - Saint Martin': '${:,.0f}',
            'Total Cost (USD) - Dutch - Sint Maarten': '${:,.0f}'
        }),
        use_container_width=True,
        hide_index=True
    )

# Charts
st.subheader("📈 Trends")

chart_df = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
    'Total Hours': 'sum',
    'Total Cost (USD)': 'sum'
}).reset_index()

chart_df['Avg Cost per Hour'] = chart_df['Total Cost (USD)'] / chart_df['Total Hours']

fig1 = px.line(
    chart_df, 
    x='Month (YYYY-MM)', 
    y='Avg Cost per Hour', 
    color='Entity',
    markers=True,
    title="Average Hourly Labor Cost Trend (USD) - Production Staff Only"
)
fig1.update_layout(yaxis_title="USD per Hour", xaxis_title="Month")
st.plotly_chart(fig1, use_container_width=True)

# OT Trend
if 'OT Hours 25%' in df.columns or 'OT Hours 50%' in df.columns:
    ot_df = df.groupby('Month (YYYY-MM)').agg({
        'OT Hours 25%': 'sum',
        'OT Hours 50%': 'sum'
    }).reset_index()
    ot_df['Total OT Hours'] = ot_df.get('OT Hours 25%', 0) + ot_df.get('OT Hours 50%', 0)
    
    fig2 = px.bar(ot_df, x='Month (YYYY-MM)', y='Total OT Hours', title="Total Overtime Hours Trend")
    st.plotly_chart(fig2, use_container_width=True)

# Detailed Data Table
st.subheader("📋 Detailed Data")

entities = df['Entity'].unique().tolist() if 'Entity' in df.columns else []
months = sorted(df['Month (YYYY-MM)'].unique().tolist()) if 'Month (YYYY-MM)' in df.columns else []

col_a, col_b = st.columns(2)
with col_a:
    selected_entities = st.multiselect("Filter by Entity", entities, default=entities)
with col_b:
    selected_months = st.multiselect("Filter by Month", months, default=months)

filtered_df = df.copy()
if selected_entities and 'Entity' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Entity'].isin(selected_entities)]
if selected_months and 'Month (YYYY-MM)' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Month (YYYY-MM)'].isin(selected_months)]

display_cols = ['Month (YYYY-MM)', 'Employee Name', 'Entity', 'Department', 'Total Hours', 'Total Cost (USD)']
available_display = [c for c in display_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[available_display].style.format({
        'Total Cost (USD)': '${:,.2f}'
    }),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Production Staff Only")
