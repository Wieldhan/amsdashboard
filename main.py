# Standard library imports
import datetime
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Data handling
import pandas as pd

# Streamlit
import streamlit as st

# Application modules - critical modules first
from src.frontend.login_page import login_page
from src.frontend.change_password import change_password_form
from src.component.sidebar import initialize_session_state, show_sidebar, reset_sidebar_rendering_state, add_title_above_nav
from src.backend.database_branch import get_branch_mapping
from src.frontend.tab_funding import show_funding_tab
from src.frontend.tab_lending import show_lending_tab

# Main dashboard function
def main_dashboard():
    """Main dashboard content for the home page"""
    # Reset sidebar rendering state 
    reset_sidebar_rendering_state()
    
    # Set current page
    st.session_state.active_page = 'Home'
    
    # Initialize session state variables for filtering
    initialize_session_state()
    
    # Add title and logo above navigation
    add_title_above_nav("AMS Dashboard")
    
    # Show change password form if requested
    if st.session_state.get('show_change_password', False):
        change_password_form()
        if st.button("Back to Dashboard", key="unique_back_btn"):
            st.session_state.show_change_password = False
            st.rerun()
        return
    
    # Show sidebar with unique prefix
    show_sidebar("home_page")
    
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
            with st.container(border=True):
                st.markdown("### 🏦 Funding Dashboard")
                st.write("View funding metrics, deposit trends, and savings analysis")
                if st.button("Go to Funding", key="goto_funding_btn", use_container_width=True):
                    st.switch_page("pages/funding_module.py")
        
    with col2:
        if "all" in tab_access or "lending" in tab_access:
            with st.container(border=True):
                st.markdown("### 💰 Lending Dashboard")
                st.write("View lending metrics, financing trends, and NPF analysis")
                if st.button("Go to Lending", key="goto_lending_btn", use_container_width=True):
                    st.switch_page("pages/lending_module.py")
    
    if "all" not in tab_access and "funding" not in tab_access and "lending" not in tab_access:
        st.warning("You don't have access to any dashboard pages.")

# Function to run funding page content
def funding_page():
    # Call the existing functionality from the pages directory
    from pages.funding_module import show_funding_content
    show_funding_content()

# Function to run lending page content
def lending_page():
    # Call the existing functionality from the pages directory
    from pages.lending_module import show_lending_content
    show_lending_content()

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

# Function to check for env vars in streamlit secrets as fallback
def get_env_var(var_name, default=None):
    # First try OS environment variables (loaded from .env)
    value = os.environ.get(var_name)
    
    # If not found, check Streamlit secrets
    if not value:
        # For database section
        if var_name.startswith("SQL_"):
            key = var_name[4:].lower()  # Remove SQL_ prefix and lowercase
            if "database" in st.secrets and key in st.secrets["database"]:
                value = st.secrets["database"][key]
        # For Supabase section
        elif var_name.startswith("SUPABASE_"):
            key = var_name[9:].lower()  # Remove SUPABASE_ prefix and lowercase
            if "supabase" in st.secrets and key in st.secrets["supabase"]:
                value = st.secrets["supabase"][key]
        # For application settings
        elif var_name in ["SYNC_INTERVAL_MINUTES", "ADMIN_DEFAULT_PASSWORD"]:
            key = var_name.lower()
            if "app" in st.secrets and key in st.secrets["app"]:
                value = st.secrets["app"][key]
    
    return value or default

# Load environment variables only once
if 'env_loaded' not in st.session_state:
    load_env_file()
    st.session_state.env_loaded = True

# Verify Supabase configuration
supabase_url = get_env_var("SUPABASE_URL")
supabase_key = get_env_var("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    st.error("Missing Supabase configuration. Please check your .env file or Streamlit secrets.")
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

# Main application logic
if not st.session_state.logged_in:
    login_page()
else:
    # Define the available pages based on user access
    home_page = st.Page(main_dashboard, title="Home", icon="🏠", default=True)
    
    # Build pages list based on access
    available_pages = [home_page]
    
    if "user_access" in st.session_state:
        tab_access = st.session_state.user_access["tab_access"].lower()
        
        # Add pages based on access rights
        if "all" in tab_access or "funding" in tab_access:
            funding_page_obj = st.Page(funding_page, title="Funding", icon="🏦")
            available_pages.append(funding_page_obj)
        
        if "all" in tab_access or "lending" in tab_access:
            lending_page_obj = st.Page(lending_page, title="Lending", icon="💰")
            available_pages.append(lending_page_obj)
    
    # Setup navigation with available pages
    pg = st.navigation(available_pages)
    pg.run()

