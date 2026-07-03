# ==================== DEPARTMENT HOURS TREND ====================
st.subheader("🏭 Hours per Department Trend (Line Chart)")

# Filter out Placement and Management just in case
dept_trend = df[df['Department'] != 'Placement'].copy()

dept_monthly = dept_trend.groupby(['Month (YYYY-MM)', 'Department']).agg({
    'Total Hours': 'sum'
}).reset_index()

fig_dept_trend = px.line(
    dept_monthly, 
    x='Month (YYYY-MM)', 
    y='Total Hours', 
    color='Department',
    markers=True,
    title="Hours per Department Over Time (Trend Lines)"
)
fig_dept_trend.update_layout(
    xaxis_title="Month",
    yaxis_title="Total Hours",
    legend_title="Department"
)
st.plotly_chart(fig_dept_trend, use_container_width=True)

# Optional: Also keep a simple total per department for latest view
st.subheader("📊 Total Hours by Department (Latest Period View)")
dept_total = dept_trend.groupby('Department').agg({
    'Total Hours': 'sum',
    'Total Cost (USD)': 'sum'
}).reset_index().sort_values('Total Hours', ascending=False)

fig_dept_bar = px.bar(
    dept_total, 
    x='Department', 
    y='Total Hours',
    title="Total Hours by Department (All Months Combined)",
    color='Department'
)
st.plotly_chart(fig_dept_bar, use_container_width=True)
