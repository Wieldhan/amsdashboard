import streamlit as st
from datetime import datetime, timedelta
from src.backend.database_branch import get_branch_mapping

def show_sidebar(key_prefix=""):
    """Create a reusable sidebar component for all pages
    
    Args:
        key_prefix (str): Prefix to add to all widget keys to ensure uniqueness
    """
    with st.sidebar:
        st.image("logo.png", use_container_width=True)
        
        # Make sure we have a valid key prefix
        if not key_prefix:
            key_prefix = st.session_state.active_page.lower() + "_"
        
        # Ensure key prefix ends with underscore
        if not key_prefix.endswith("_"):
            key_prefix += "_"
        
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
                "",
                options=available_branch_codes,
                default=st.session_state.sidebar_branch_selector,
                format_func=lambda x: branches.get(x, x),
                key=f"{key_prefix}branch_selector_input",
                selection_mode="multi"
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