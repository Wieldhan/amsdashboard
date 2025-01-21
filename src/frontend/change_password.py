import streamlit as st
from src.backend.user_management import UserManagement

def change_password_form():
    # Initialize user management
    user_mgmt = UserManagement()
    
    with st.form("change_password"):
        st.subheader("Change Password")
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if new_password != confirm_password:
                st.error("New passwords don't match")
            elif user_mgmt.change_password(st.session_state.user_id, old_password, new_password):
                st.success("Password changed successfully")
            else:
                st.error("Current password is incorrect") 