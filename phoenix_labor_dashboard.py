# ==================== EMPLOYEE → DEPARTMENT TABLE ====================
st.subheader("👥 Employee → Department Overview")

# Checkbox to filter only active employees
show_only_active = st.checkbox("Show only currently active employees (hide people who left)", value=True)

emp_dept = df[['Employee Name', 'Department', 'Entity', 'Month (YYYY-MM)']].copy()

if show_only_active:
    # Get the latest month in the data
    latest_month = df['Month (YYYY-MM)'].max()
    active_employees = df[df['Month (YYYY-MM)'] == latest_month]['Employee Name'].unique()
    emp_dept = emp_dept[emp_dept['Employee Name'].isin(active_employees)].copy()
    st.caption(f"Showing only employees active in {latest_month}")
else:
    st.caption("Showing all employees (including people who have left)")

# Clean table - drop duplicates and sort
emp_dept = emp_dept[['Employee Name', 'Department', 'Entity']].drop_duplicates().sort_values(
    ['Entity', 'Department', 'Employee Name']
)

# Color the Department column
def color_department(val):
    colors = {
        'Slab/Wall production': 'background-color: #d4edda',      # light green
        'Beam/Stairs production': 'background-color: #cce5ff',    # light blue
        'Beam/Stairs Rebar': 'background-color: #fff3cd',         # light yellow
        'Slab/Wall Rebar': 'background-color: #f8d7da',           # light red/pink
        'Support': 'background-color: #e2e3e5',                   # light gray
        'Crane operator': 'background-color: #d1ecf1',            # light cyan
        'Placement': 'background-color: #fdebd0',                 # light orange
    }
    return colors.get(val, '')

st.dataframe(
    emp_dept.style.applymap(color_department, subset=['Department']),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Employee Name": st.column_config.TextColumn("Employee Name", width="large"),
        "Department": st.column_config.TextColumn("Department", width="medium"),
        "Entity": st.column_config.TextColumn("Entity", width="medium"),
    }
)
