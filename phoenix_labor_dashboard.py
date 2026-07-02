import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Phoenix Labor Dashboard", page_icon="🏗️", layout="wide")

st.title("🏗️ Phoenix Labor Cost Dashboard")
st.markdown("**Production Staff Only** — Management & Owners excluded")

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
        
        # Calculate Total Cost (USD) ourselves (most important fix)
        if 'Total Employer Cost (Local)' in df.columns and 'Exchange Rate to USD' in df.columns:
            df['Total Cost (USD)'] = df['Total Employer Cost (Local)'] * df['Exchange Rate to USD']
        else:
            df['Total Cost (USD)'] = 0
        
        # Filter Production Only
        if 'Production_Only (Yes/No)' in df.columns:
            df = df[df['Production_Only (Yes/No)'] == 'Yes'].copy()
        
        # ==================== KPIs ====================
        col1, col2, col3, col4 = st.columns(4)
        total_hours = df['Total Hours'].sum()
        total_cost = df['Total Cost (USD)'].sum()
        avg_cost = total_cost / total_hours if total_hours > 0 else 0
        
        col1.metric("Total Production Hours", f"{total_hours:,.0f}")
        col2.metric("Total Labor Cost (USD)", f"${total_cost:,.0f}")
        col3.metric("Avg Cost per Hour", f"${avg_cost:.2f}")
        col4.metric("Months Loaded", df['Month (YYYY-MM)'].nunique())
        
        st.markdown("---")
        
        # ==================== MONTHLY COMPARISON ====================
        st.subheader("📊 Monthly French vs Dutch Comparison")
        
        monthly = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
            'Total Hours': 'sum',
            'Total Cost (USD)': 'sum'
        }).reset_index()
        
        if not monthly.empty:
            pivot = monthly.pivot(index='Month (YYYY-MM)', columns='Entity', 
                                  values=['Total Hours', 'Total Cost (USD)'])
            pivot.columns = [f"{c[0]} ({c[1]})" for c in pivot.columns]
            pivot = pivot.reset_index()
            st.dataframe(pivot.style.format({
                'Total Cost (USD) (French - Saint Martin)': '${:,.0f}',
                'Total Cost (USD) (Dutch - Sint Maarten)': '${:,.0f}'
            }))
        
        # ==================== CHART ====================
        st.subheader("📈 Average Hourly Cost Trend")
        
        chart_df = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
            'Total Hours': 'sum',
            'Total Cost (USD)': 'sum'
        }).reset_index()
        chart_df['Avg $/hr'] = chart_df['Total Cost (USD)'] / chart_df['Total Hours']
        
        fig = px.line(chart_df, x='Month (YYYY-MM)', y='Avg $/hr', color='Entity', 
                      markers=True, title="Average Hourly Labor Cost Trend (USD)")
        st.plotly_chart(fig, use_container_width=True)
        
        # ==================== DETAILED TABLE ====================
        st.subheader("📋 Detailed Data")
        st.dataframe(
            df[['Month (YYYY-MM)', 'Employee Name', 'Entity', 'Department', 
                'Total Hours', 'Total Cost (USD)']].style.format({'Total Cost (USD)': '${:,.2f}'}),
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

else:
    st.info("Please upload the Excel file to see the dashboard.")
