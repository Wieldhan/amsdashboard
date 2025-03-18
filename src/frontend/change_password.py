import streamlit as st
from src.backend.supabase_client import get_supabase_client
import logging
import hashlib

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def change_password_form():
    with st.form("change_password", clear_on_submit=True):
        st.subheader("Change Password")
        current_password = st.text_input(
            "Current Password", 
            type="password",
            value=""
        )
        new_password = st.text_input(
            "New Password", 
            type="password",
            value=""
        )
        confirm_password = st.text_input(
            "Confirm New Password", 
            type="password",
            value=""
        )
        
        if st.form_submit_button("Change Password"):
            if not current_password or not new_password or not confirm_password:
                st.error("Please fill in all password fields")
                return
                
            if new_password != confirm_password:
                st.error("New passwords don't match")
                return
                
            if len(new_password) < 6:
                st.error("New password must be at least 6 characters long")
                return
                
            try:
                # Get Supabase client with service role for secure access
                supabase = get_supabase_client(use_service_role=True)
                
                try:
                    # Get current user data
                    user_response = supabase.table('users').select('*').eq('user_id', st.session_state.user_id).single().execute()
                    user_data = user_response.data
                    
                    if not user_data:
                        st.error("User not found. Please contact administrator.")
                        return
                    
                    # Verify current password
                    if user_data.get('password_hash') != hash_password(current_password):
                        st.error("Current password is incorrect")
                        return
                    
                    # Update password
                    supabase.table('users').update({
                        'password_hash': hash_password(new_password)
                    }).eq('user_id', st.session_state.user_id).execute()
                    
                    st.success("Password changed successfully! Please use your new password next time you login.")
                    
                except Exception as e:
                    logging.error(f"Error updating password: {str(e)}")
                    st.error("Failed to update password. Please try again later.")
                    
            except ValueError as ve:
                st.error(str(ve))  # Show configuration errors
            except Exception as e:
                logging.error(f"Password change error: {str(e)}")
                st.error("Failed to change password. Please try again later or contact administrator.") 