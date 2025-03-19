import streamlit as st
import os
import sys

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.frontend.tab_funding import show_funding_tab
from src.component.sidebar import initialize_session_state, show_sidebar, reset_sidebar_rendering_state, add_title_above_nav
from src.frontend.change_password import change_password_form

def show_funding_content():
    """Wrapper function for funding content to be called from st.Page navigation"""
    # Reset sidebar rendering state when changing pages
    reset_sidebar_rendering_state()
    
    # Set active page
    st.session_state.active_page = 'Funding'
    
    # Initialize session state only if needed - preserves values from other pages
    initialize_session_state()
    
    # Add title and logo above navigation
    add_title_above_nav("AMS Dashboard")
    
    # Show change password or dashboard
    if st.session_state.get('show_change_password', False):
        change_password_form()
        if st.button("Back to Dashboard", key="funding_back_btn"):
            st.session_state.show_change_password = False
            st.rerun()
    else:
        # Show sidebar with fixed key prefix (no timestamps)
        show_sidebar("funding_page")
        
        # Show funding tab content directly as the main page
        show_funding_tab() 