import streamlit as st
from src.frontend.tab_lending import show_lending_tab

# Set page config
st.set_page_config(
    page_title="AMS Lending Dashboard",
    page_icon="💸",
    layout="wide"
)

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first")
    st.stop()

# Check access permission
if 'user_access' not in st.session_state or not ('all' in st.session_state.user_access['tab_access'].lower() or 'lending' in st.session_state.user_access['tab_access'].lower()):
    st.error("You don't have access to this page")
    st.stop()

# Show the lending dashboard
show_lending_tab() 