import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Phoenix Labor Dashboard", page_icon="🏗️", layout="wide")

st.title("🏗️ Phoenix Labor Cost Dashboard")
st.markdown("**Production Staff Only** — Management & Owners excluded")

# File uploader (always visible)
uploaded_file = st.file_uploader(
    "Upload your Phoenix Labor Cost Tracker Clean Excel file",
    type=["xlsx"]
)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Labor_Data_Entry")
        df.columns = [str(c).strip() for c in df.columns]
        
        # Calculate Total Hours
        df['Total Hours'] = (
            df.get('Regular Hours', 0).fillna(0) +
            df.get('OT Hours 25%', 0).fillna(0) +
            df.get('OT Hours 50%', 0).fillna(0)
        )
        
        # Filter Production Only
        if 'Production_Only (Yes/No)' in df.columns:
            df = df[df['Production_Only (Yes/No)'] == 'Yes'].copy()
        
        st.success("File loaded successfully!")
        
        # Show basic info
        st.write(f"**Total rows:** {len(df)}")
        st.write(f"**Months available:** {df['Month (YYYY-MM)'].nunique()}")
        
        # Simple table
        st.subheader("Data Preview")
        st.dataframe(df.head(20))
        
    except Exception as e:
        st.error(f"Error reading the file: {e}")

else:
    st.info("Please upload the Excel file to see the dashboard.")st.sidebar.metric("XCG → USD (Peg)", f"${xcg_usd}")
st.sidebar.info("XCG is pegged to USD.")

# Main
st.title("🏗️ Phoenix Labor Cost Dashboard")
st.markdown("**Production Staff Only** — Management & Owners excluded")

if df.empty:
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)
total_hours = df['Total Hours'].sum()
total_cost = df.get('Total Cost (USD)', pd.Series([0])).sum()
avg_hourly = total_cost / total_hours if total_hours > 0 else 0

col1.metric("Total Production Hours", f"{total_hours:,.0f}")
col2.metric("Total Labor Cost (USD)", f"${total_cost:,.0f}")
col3.metric("Overall Avg Cost/Hour", f"${avg_hourly:.2f}")
col4.metric("Months of Data", df['Month (YYYY-MM)'].nunique())

st.markdown("---")

# Monthly Comparison
st.subheader("📊 Monthly French vs Dutch Comparison")

summary = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
    'Total Hours': 'sum',
    'Total Cost (USD)': 'sum'
}).reset_index()

if not summary.empty:
    pivot = summary.pivot(index='Month (YYYY-MM)', columns='Entity', values=['Total Hours', 'Total Cost (USD)'])
    pivot.columns = [f"{c[0]} - {c[1]}" for c in pivot.columns]
    pivot = pivot.reset_index()
    
    if 'Total Cost (USD) - French - Saint Martin' in pivot.columns:
        pivot['French Avg $/hr'] = pivot['Total Cost (USD) - French - Saint Martin'] / pivot['Total Hours - French - Saint Martin']
    if 'Total Cost (USD) - Dutch - Sint Maarten' in pivot.columns:
        pivot['Dutch Avg $/hr'] = pivot['Total Cost (USD) - Dutch - Sint Maarten'] / pivot['Total Hours - Dutch - Sint Maarten']
    
    st.dataframe(pivot.style.format({'French Avg $/hr': '${:.2f}', 'Dutch Avg $/hr': '${:.2f}'}), use_container_width=True)

# Charts
st.subheader("📈 Average Hourly Cost Trend")

chart_df = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
    'Total Hours': 'sum',
    'Total Cost (USD)': 'sum'
}).reset_index()
chart_df['Avg $/hr'] = chart_df['Total Cost (USD)'] / chart_df['Total Hours']

fig = px.line(chart_df, x='Month (YYYY-MM)', y='Avg $/hr', color='Entity', markers=True,
              title="Average Hourly Labor Cost (USD) - Production Staff Only")
st.plotly_chart(fig, use_container_width=True)

# Detailed Table
st.subheader("📋 Detailed Data")

filtered = df.copy()
st.dataframe(
    filtered[['Month (YYYY-MM)', 'Employee Name', 'Entity', 'Department', 'Total Hours', 'Total Cost (USD)']].style.format({
        'Total Cost (USD)': '${:,.2f}'
    }),
    use_container_width=True,
    hide_index=True
)
