# Standard library imports
import datetime
from datetime import datetime, timedelta
import os

# Data handling
import pandas as pd

# Streamlit
import streamlit as st

# Application modules - critical modules first
from src.frontend.login_page import login_page
from src.frontend.change_password import change_password_form
from src.component.sidebar import initialize_session_state, show_sidebar
from src.backend.database_branch import get_branch_mapping
from src.frontend.tab_funding import show_funding_tab
from src.frontend.tab_lending import show_lending_tab

# Configure the navigation
if "logged_in" in st.session_state and st.session_state.logged_in:
    # Set up navigation with proper page names and icons
    pages = [
        st.Page("main.py", title="Home", icon="🏠"),
        st.Page("pages/1_Funding.py", title="Funding", icon="🏦"),
        st.Page("pages/2_Lending.py", title="Lending", icon="💰"),
    ]
    
    # Get user access to filter available pages
    if "user_access" in st.session_state:
        tab_access = st.session_state.user_access["tab_access"].lower()
        filtered_pages = [pages[0]]  # Always keep Home
        
        if "all" in tab_access or "funding" in tab_access:
            filtered_pages.append(pages[1])
        
        if "all" in tab_access or "lending" in tab_access:
            filtered_pages.append(pages[2])
        
        # Set the navigation with filtered pages
        page = st.navigation(filtered_pages)
    else:
        # If no user access defined yet, just show Home
        page = st.navigation([pages[0]])

# Load environment variables
def load_env_file(path=".env"):
    try:
        if not os.path.exists(path):
            st.warning(f"Environment file {path} not found")
            return
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Strip quotes if present
                    value = value.strip('"\'')
                    key = key.strip()
                    os.environ[key] = value
        return True
    except Exception as e:
        st.warning(f"Error loading environment variables: {str(e)}")
        return False

# Load environment variables only once
if 'env_loaded' not in st.session_state:
    load_env_file()
    st.session_state.env_loaded = True

# Verify Supabase configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    st.error("Missing Supabase configuration. Please check your .env file.")
    st.stop()

# Load initial data for global use
all_branches = get_branch_mapping()
all_branch_codes = list(all_branches.keys()) if all_branches else []

# Basic session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_access' not in st.session_state:
    st.session_state.user_access = None
if 'show_change_password' not in st.session_state:
    st.session_state.show_change_password = False
if 'active_page' not in st.session_state:
    st.session_state.active_page = 'Home'

# Main dashboard function
def main_dashboard():
    # Set current page
    st.session_state.active_page = 'Home'
    
    # Initialize session state variables for filtering
    initialize_session_state()
    
    # Show change password form if requested
    if st.session_state.get('show_change_password', False):
        change_password_form()
        if st.button("Back to Dashboard", key="unique_back_btn"):
            st.session_state.show_change_password = False
            st.rerun()
        return
    
    # Show sidebar with user info
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.user_id}")
        st.markdown("---")
    
    # Show sidebar filters with unique keys
    sidebar_key = "main_sidebar"
    show_sidebar(sidebar_key)
    
    # Main content - Home page
    st.title("🏠 AMS Dashboard")
    st.markdown("""
    Welcome to the AMS Dashboard! Use the navigation menu to access different dashboard pages.
    """)
    
    # Get user tab access
    tab_access = st.session_state.user_access["tab_access"].lower()
    
    # Create navigation links to pages with improved styling
    st.markdown("### Dashboard Navigation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "all" in tab_access or "funding" in tab_access:
            st.markdown("""
            ### [🏦 Funding Dashboard](/Funding)
            View funding metrics, deposit trends, and savings analysis
            """)
        
    with col2:
        if "all" in tab_access or "lending" in tab_access:
            st.markdown("""
            ### [💰 Lending Dashboard](/Lending)
            View lending metrics, financing trends, and NPF analysis
            """)
    
    if "all" not in tab_access and "funding" not in tab_access and "lending" not in tab_access:
        st.warning("You don't have access to any dashboard pages.")

# Main application logic
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()
    
    # Add this at the end to actually run the current page
    if "logged_in" in st.session_state and st.session_state.logged_in:
        if 'page' in locals():
            page.run()

