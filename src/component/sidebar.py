import streamlit as st
import time
from datetime import datetime, timedelta
from src.backend.database_branch import get_branch_mapping

def add_title_above_nav(title="AMS Dashboard"):
    """Add logo and title above navigation using CSS only"""
    # Get the user ID for the welcome message
    username = st.session_state.get('user_id', 'admin')
    
    # Create a single CSS block that handles everything
    st.markdown(
        f"""
        <style>
            /* Style the navigation with logo and padding */
            [data-testid="stSidebarNav"] {{
                background-image: url(https://i.imgur.com/NMN7YD9.png);
                background-repeat: no-repeat;
                background-size: 220px auto;
                margin-top: -20px;
                padding-top: 100px;
                background-position: center 20px;
            }}
            
            /* Add title text below the logo */
            [data-testid="stSidebarNav"]::before {{
                content: "{title}";
                margin-left: 20px;
                font-size: 28px;
                position: relative;
                font-weight: bold;
                top: 5px;
                display: block;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                width: 85%;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            
            /* Push the navigation items down */
            [data-testid="stSidebarNav"] > ul {{
                padding-top: 0px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_sidebar(key_prefix=""):
    """Create a reusable sidebar component for all pages
    
    Args:
        key_prefix (str): Prefix to add to all widget keys to ensure uniqueness
    """
    # Make sure we have a valid key prefix
    if not key_prefix:
        key_prefix = st.session_state.active_page.lower() + "_"
    
    # Ensure key prefix ends with underscore
    if not key_prefix.endswith("_"):
        key_prefix += "_"
    
    # Check if this sidebar prefix has already been rendered to avoid duplicates
    sidebar_key = f"sidebar_rendered_{key_prefix}"
    if sidebar_key in st.session_state and st.session_state[sidebar_key]:
        return
    
    # Mark this sidebar as rendered
    st.session_state[sidebar_key] = True
    
    with st.sidebar:
        # Welcome message after navigation with custom styling
        if 'user_id' in st.session_state:
            st.markdown(f'<div class="welcome-msg">Welcome, {st.session_state.user_id}</div>', unsafe_allow_html=True)
        
        # Filter section
        st.markdown("### 🔍 Filter Data")
        
        # Date Range - save changes to session state for persistence across pages
        start_date = st.date_input(
            "📅 Periode Awal",
            value=st.session_state.start_date,
            key=f"{key_prefix}start_date_input"
        )
        # Update session state after widget interaction
        st.session_state.start_date = start_date
        
        end_date = st.date_input(
            "📅 Periode Akhir",
            value=st.session_state.end_date,
            key=f"{key_prefix}end_date_input"
        )
        # Update session state after widget interaction
        st.session_state.end_date = end_date
        
        # Period Selection
        period_options = ["Hari", "Minggu", "Bulan", "Tahun"]
        period = st.selectbox(
            "⏱️ Satuan Analisis:",
            period_options,
            index=period_options.index(st.session_state.overview_period),
            key=f"{key_prefix}overview_period_input"
        )
        # Update session state after widget interaction
        st.session_state.overview_period = period
        
        # Branch Selection
        branches = get_branch_mapping()
        branch_access = st.session_state.user_access["branch_access"] if 'user_access' in st.session_state else "all"
        
        if "all" in branch_access:
            available_branch_codes = list(branches.keys()) if branches else []
        else:
            available_branch_codes = branch_access.split(",")
            
        if branches:
            st.markdown("🏢 **Filter Cabang:**")
            selected_branches = st.pills(
                "Filter Branch",
                options=available_branch_codes,
                default=st.session_state.sidebar_branch_selector,
                format_func=lambda x: branches.get(x, x),
                key=f"{key_prefix}branch_selector_input",
                selection_mode="multi",
                label_visibility="collapsed"
            )
            # Update session state after widget interaction
            st.session_state.sidebar_branch_selector = selected_branches
        else:
            st.error("No branch data available")
        
        # Create space before user account section
        st.markdown("---")
        st.markdown("## 👤 User Account")
        
        # Add change password button
        if st.button("🔑 Change Password", use_container_width=True, key=f"{key_prefix}change_password_btn"):
            st.session_state.show_change_password = True
            st.rerun()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True, key=f"{key_prefix}logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_access = None
            st.rerun()

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    # Get branch data first
    branches = get_branch_mapping()
    
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime.now().date() - timedelta(days=30)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime.now().date()
    if 'overview_period' not in st.session_state:
        st.session_state.overview_period = "Hari"
    if 'sidebar_branch_selector' not in st.session_state:
        branch_access = st.session_state.user_access["branch_access"] if 'user_access' in st.session_state else "all"
        
        if "all" in branch_access:
            available_branch_codes = list(branches.keys()) if branches else []
        else:
            available_branch_codes = branch_access.split(",")
            
        st.session_state.sidebar_branch_selector = available_branch_codes

def reset_sidebar_rendering_state():
    """Reset all sidebar rendering state flags to ensure sidebar refreshes between pages"""
    for key in list(st.session_state.keys()):
        if key.startswith("sidebar_rendered_"):
            del st.session_state[key] 