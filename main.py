# Standard library imports
import datetime
from datetime import datetime

# Data handling
import pandas as pd

# Streamlit
import streamlit as st

# Set page config - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="AMS Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import tab modules
from src.frontend.tab_funding import show_funding_tab
from src.frontend.tab_lending import show_lending_tab
from src.backend.database_branch import get_branch_mapping
from src.frontend.login_page import login_page
from src.frontend.change_password import change_password_form

# Load initial data for global use
all_branches = get_branch_mapping()
all_branch_codes = list(all_branches.keys())

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_access' not in st.session_state:
    st.session_state.user_access = None

def main_dashboard():
    # Sidebar
    with st.sidebar:
        st.image("logo.png", use_container_width=True)
        st.title("AMS Dashboard")
        
        # User info
        st.write(f"Welcome, {st.session_state.user_id}")
        
        # Date inputs
        current_date = datetime(2021, 6, 30)  # Hardcoded for dummy database
        one_month_ago = current_date - pd.DateOffset(months=1)
        min_date = datetime(2020, 1, 1)
        
        start_date = st.date_input(
            "Periode Awal",
            value=one_month_ago,
            key="start_date",
            min_value=min_date
        )
        
        end_date = st.date_input(
            "Periode Akhir",
            value=current_date,
            key="end_date"
        )
        
        if start_date > end_date:
            st.error("Error: End date must fall after start date.")
            st.stop()
                
        st.selectbox("Satuan Analisis:", ["Hari", "Minggu", "Bulan", "Tahun"], key="overview_period")
        
        # Filter branches based on user access
        branch_access = st.session_state.user_access["branch_access"]
        if "all" in branch_access:
            available_branch_codes = all_branch_codes
        else:
            available_branch_codes = branch_access.split(",")
        
        st.pills(
            "Filter Cabang:", 
            options=available_branch_codes,
            format_func=lambda x: all_branches[x],
            selection_mode="multi",
            default=available_branch_codes,
            key="sidebar_branch_selector"
        )
        
        # Add empty space to push logout to bottom
        st.markdown("---")
        st.markdown("<br>" * 1, unsafe_allow_html=True)
        
        # Change password button
        if st.button("Change Password", use_container_width=True):
            st.session_state.show_change_password = True
            st.rerun()
        
        # Logout button at the bottom
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_access = None
            st.rerun()

    # Show change password or dashboard
    if st.session_state.get('show_change_password', False):
        change_password_form()
        if st.button("Back to Dashboard"):
            st.session_state.show_change_password = False
            st.rerun()
    else:
        # Main content - Home page
        st.title("Welcome to AMS Dashboard")
        st.write("Please select a page from the sidebar to view detailed information.")
        
        # Display available pages based on user access
        st.subheader("Available Pages:")
        
        tab_access = st.session_state.user_access["tab_access"].lower()
        col1, col2 = st.columns(2)
        
        with col1:
            if "all" in tab_access or "funding" in tab_access:
                st.info("💰 **Funding Dashboard**\n\nView detailed funding information including deposits and savings.")
                
        with col2:
            if "all" in tab_access or "lending" in tab_access:
                st.info("💸 **Lending Dashboard**\n\nAnalyze lending data including financing and rahn information.")

# Main app logic
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()

