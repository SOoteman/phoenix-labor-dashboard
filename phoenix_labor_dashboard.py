import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Phoenix Labor Dashboard", page_icon="🏗️", layout="wide")

st.title("🏗️ Phoenix Labor Cost Dashboard")
st.markdown("**Production Staff Only** — Management & Owners excluded")

# File uploader
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
        
        # Show summary
        st.write(f"**Total rows loaded:** {len(df)}")
        st.write(f"**Months available:** {df['Month (YYYY-MM)'].nunique()}")
        
        # Show data
        st.subheader("Data Preview")
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"Error reading the file: {str(e)}")

else:
    st.info("Please upload the Excel file to see the dashboard.")
