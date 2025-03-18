import streamlit as st
from src.frontend.tab_lending import show_lending_tab
from src.component.sidebar import initialize_session_state, show_sidebar
from src.frontend.change_password import change_password_form

# Set active page
st.session_state.active_page = 'Lending'

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first")
    st.stop()

# Check access permission
if 'user_access' not in st.session_state or not ('all' in st.session_state.user_access['tab_access'].lower() or 'lending' in st.session_state.user_access['tab_access'].lower()):
    st.error("You don't have access to this page")
    st.stop()

# Initialize session state only if needed - preserves values from other pages
initialize_session_state()

# Show change password or dashboard
if st.session_state.get('show_change_password', False):
    change_password_form()
    if st.button("Back to Dashboard", key="lending_back_btn"):
        st.session_state.show_change_password = False
        st.rerun()
else:
    # Show user info in sidebar
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.user_id}")
        st.markdown("---")
        
    # Show sidebar with unique keys
    show_sidebar("lending_page")
    
    # Show lending tab content directly as the main page
    show_lending_tab() 