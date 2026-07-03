import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Phoenix Labor Dashboard", page_icon="🏗️", layout="wide")

st.title("🏗️ Phoenix Labor Cost Dashboard")
st.markdown("**Production Staff Only** — Management & Placement excluded")

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
        
        # Calculate Total Cost (USD)
        gross = df.get('Gross Pay (Local)', 0).fillna(0)
        charges = df.get('Employer Charges (Local)', 0).fillna(0)
        exchange = df.get('Exchange Rate to USD', 0.558).fillna(0.558)
        df['Total Cost (USD)'] = (gross + charges) * exchange
        
        # Filter Production Only + exclude Placement
        if 'Production_Only (Yes/No)' in df.columns:
            df = df[df['Production_Only (Yes/No)'] == 'Yes'].copy()
        
        # Exclude Placement department
        if 'Department' in df.columns:
            df = df[df['Department'] != 'Placement'].copy()
        
        # ==================== KPIs ====================
        col1, col2, col3, col4 = st.columns(4)
        total_hours = df['Total Hours'].sum()
        total_cost = df['Total Cost (USD)'].sum()
        avg_cost = total_cost / total_hours if total_hours > 0 else 0
        unique_employees = df['Employee Name'].nunique()
        
        col1.metric("Total Production Hours", f"{total_hours:,.0f}")
        col2.metric("Total Labor Cost (USD)", f"${total_cost:,.0f}")
        col3.metric("Avg Cost per Hour", f"${avg_cost:.2f}")
        col4.metric("Active Employees (Latest Month)", unique_employees)
        
        st.markdown("---")
        
        # ==================== NEW CHARTS ====================
        
        # 1. Average Cost per Hour Trend (Dutch + French + Total)
        st.subheader("📈 Average Cost per Hour Trend (Dutch vs French vs Total)")
        
        cost_trend = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
            'Total Hours': 'sum',
            'Total Cost (USD)': 'sum'
        }).reset_index()
        cost_trend['Avg $/hr'] = cost_trend['Total Cost (USD)'] / cost_trend['Total Hours']
        
        # Create Total line
        total_cost_line = cost_trend.groupby('Month (YYYY-MM)').agg({
            'Total Hours': 'sum',
            'Total Cost (USD)': 'sum'
        }).reset_index()
        total_cost_line['Avg $/hr'] = total_cost_line['Total Cost (USD)'] / total_cost_line['Total Hours']
        total_cost_line['Entity'] = 'Total (Both Sides)'
        
        cost_trend_combined = pd.concat([cost_trend, total_cost_line], ignore_index=True)
        
        fig_avg = px.line(cost_trend_combined, x='Month (YYYY-MM)', y='Avg $/hr', 
                          color='Entity', markers=True,
                          title="Average Cost per Hour Trend")
        st.plotly_chart(fig_avg, use_container_width=True)
        
        # 2. Monthly Total Cost Trend + Employee Count
        st.subheader("💰 Monthly Total Labor Cost Trend + Active Employees")
        
        monthly_cost = df.groupby('Month (YYYY-MM)').agg({
            'Total Cost (USD)': 'sum',
            'Employee Name': 'nunique'
        }).reset_index()
        monthly_cost.columns = ['Month (YYYY-MM)', 'Total Cost (USD)', 'Active Employees']
        
        # Create figure with secondary y-axis for employee count
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig_cost = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_cost.add_trace(
            go.Bar(x=monthly_cost['Month (YYYY-MM)'], y=monthly_cost['Total Cost (USD)'],
                   name="Total Labor Cost (USD)", marker_color="#1f77b4"),
            secondary_y=False
        )
        
        fig_cost.add_trace(
            go.Scatter(x=monthly_cost['Month (YYYY-MM)'], y=monthly_cost['Active Employees'],
                       name="Active Employees", mode='lines+markers', line=dict(color='red', width=3)),
            secondary_y=True
        )
        
        fig_cost.update_layout(
            title_text="Monthly Total Labor Cost + Number of Active Employees",
            xaxis_title="Month"
        )
        fig_cost.update_yaxes(title_text="Total Cost (USD)", secondary_y=False)
        fig_cost.update_yaxes(title_text="Number of Employees", secondary_y=True)
        
        st.plotly_chart(fig_cost, use_container_width=True)
        
        # ==================== EXISTING CHARTS (kept) ====================
        # Overtime by Entity
        st.subheader("📊 Overtime Hours by Entity")
        ot_entity = df.groupby(['Month (YYYY-MM)', 'Entity']).agg({
            'OT Hours 25%': 'sum',
            'OT Hours 50%': 'sum'
        }).reset_index()
        ot_entity['Total OT Hours'] = ot_entity['OT Hours 25%'] + ot_entity['OT Hours 50%']
        
        fig_ot = px.bar(ot_entity, x='Month (YYYY-MM)', y='Total OT Hours', 
                        color='Entity', barmode='group')
        st.plotly_chart(fig_ot, use_container_width=True)
        
        # Overtime per Person (Top 12)
        st.subheader("👤 Overtime Trend per Person (Top 12)")
        person_ot = df.groupby(['Month (YYYY-MM)', 'Employee Name']).agg({
            'OT Hours 25%': 'sum',
            'OT Hours 50%': 'sum'
        }).reset_index()
        person_ot['Total OT Hours'] = person_ot['OT Hours 25%'] + person_ot['OT Hours 50%']
        
        top_people = person_ot.groupby('Employee Name')['Total OT Hours'].sum().nlargest(12).index.tolist()
        person_ot_filtered = person_ot[person_ot['Employee Name'].isin(top_people)]
        
        fig_person = px.line(person_ot_filtered, x='Month (YYYY-MM)', y='Total OT Hours',
                             color='Employee Name', markers=True)
        st.plotly_chart(fig_person, use_container_width=True)
        
        # Hours per Department (excluding Placement)
        st.subheader("🏭 Hours per Department (Placement excluded)")
        dept_hours = df.groupby('Department').agg({
            'Total Hours': 'sum',
            'Total Cost (USD)': 'sum'
        }).reset_index().sort_values('Total Hours', ascending=False)
        
        fig_dept = px.bar(dept_hours, x='Department', y='Total Hours')
        st.plotly_chart(fig_dept, use_container_width=True)
        
        # Detailed Table
        st.subheader("📋 Detailed Data (Placement excluded)")
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
