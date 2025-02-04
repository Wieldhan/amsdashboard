# Standard library imports
import datetime
from datetime import datetime

# Data handling
import pandas as pd

# Streamlit
import streamlit as st

# Set page title and layout - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="AMS Dashboard", layout="wide", page_icon="📊")

# Import tab modules
from src.frontend.tab_funding import show_funding_tab
from src.frontend.tab_lending import show_lending_tab
from src.backend.database_branch import get_branch_mapping
from src.backend.user_management import UserManagement
from src.frontend.login_page import login_page
from src.frontend.user_management_page import user_management_page
from src.frontend.data_management_page import data_management_page
from src.frontend.change_password import change_password_form

# Initialize user management
user_mgmt = UserManagement()

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
        
        # Admin section
        if st.session_state.user_access["is_admin"]:
            if st.button("User Management", use_container_width=True):
                st.session_state.show_user_management = True
                st.rerun()
            if st.button("Data Management", use_container_width=True):
                st.session_state.show_data_management = True
                st.rerun()
        
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

    # Show user management, data management, change password, or dashboard
    if st.session_state.get('show_user_management', False):
        if st.session_state.user_access["is_admin"]:
            user_management_page(all_branch_codes, all_branches)
            if st.button("Back to Dashboard"):
                st.session_state.show_user_management = False
                st.rerun()
    elif st.session_state.get('show_data_management', False):
        if st.session_state.user_access["is_admin"]:
            data_management_page()
            if st.button("Back to Dashboard"):
                st.session_state.show_data_management = False
                st.rerun()
    elif st.session_state.get('show_change_password', False):
        change_password_form()
        if st.button("Back to Dashboard"):
            st.session_state.show_change_password = False
            st.rerun()
    else:
        # Get available tabs based on user access
        available_tabs = []
        tab_access = st.session_state.user_access["tab_access"]
        if isinstance(tab_access, str):  # Check if it's a string first
            tab_access = tab_access.lower()  # Convert to lowercase for case-insensitive comparison
            if "all" in tab_access or "funding" in tab_access:
                available_tabs.append(":material/account_balance: Funding")
            if "all" in tab_access or "lending" in tab_access:
                available_tabs.append(":material/payments: Lending")
        

        # Only create tabs if there are available ones
        if available_tabs:
            tabs = st.tabs(available_tabs)
            # Render appropriate content based on selected tab
            for tab, name in zip(tabs, available_tabs):
                with tab:
                    if name == ":material/account_balance: Funding":
                        show_funding_tab()
                    elif name == ":material/payments: Lending":
                        show_lending_tab()
        else:
            st.warning("You don't have access to any tabs. Please contact your administrator.")

# Main app logic
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()

