import streamlit as st
from src.backend.supabase_client import get_supabase_client
import logging
import hashlib

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_admin_user():
    """Ensure admin user exists in Database"""
    try:
        # Use service role client for admin operations
        supabase = get_supabase_client(use_service_role=True)
        
        admin_id = "admin"
        admin_password = "admin123"  # Default password
        
        try:
            # Check if admin exists in users table
            user_response = supabase.table('users').select('*').eq('user_id', admin_id).execute()
            
            if not user_response.data:
                # Create admin in users table
                supabase.table('users').insert({
                    'user_id': admin_id,
                    'password_hash': hash_password(admin_password),
                    'branch_access': 'all',
                    'tab_access': 'all'
                }).execute()
                logging.info("Admin user created in database")
            else:
                logging.info("Admin user exists in database")
                
        except Exception as e:
            logging.error(f"Error ensuring admin in database: {str(e)}")
            raise
                
    except Exception as e:
        logging.error(f"Error ensuring admin user: {str(e)}")
        raise

def login_page():
    # Ensure admin user exists
    try:
        ensure_admin_user()
    except Exception as e:
        st.error("Error initializing system. Please contact administrator.")
        logging.error(f"Initialization error: {str(e)}")
        return
    
    # Create three columns with the middle one having a fixed width
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Container for login form
        with st.container():
            # Center the logo and limit its size
            col1_img, col2_img, col3_img = st.columns([1, 2, 1])
            with col2_img:
                st.image("logo.png")
            
            # Title with custom CSS for centering
            st.markdown("<h1 style='text-align: center;'>AMS Dashboard Login</h1>", unsafe_allow_html=True)
            
            # Add some spacing
            st.write("")
            
            # Login form with custom styling
            with st.form("login_form"):
                user_id = st.text_input("User ID")
                password = st.text_input("Password", type="password")
                
                # Center the login button and make it more prominent
                col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])
                with col2_btn:
                    submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if not user_id or not password:
                        st.error("Please enter both User ID and password")
                        return
                        
                    try:
                        # Get Supabase client with service role for secure access
                        supabase = get_supabase_client(use_service_role=True)
                        
                        # Get user data and verify password
                        try:
                            user_response = supabase.table('users').select('*').eq('user_id', user_id).single().execute()
                            user_data = user_response.data
                            
                            if not user_data:
                                st.error("Invalid User ID or password")
                                return
                                
                            # Verify password
                            if user_data.get('password_hash') != hash_password(password):
                                st.error("Invalid User ID or password")
                                return
                            
                            # Set session state
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_access = {
                                "branch_access": user_data.get('branch_access', 'all'),
                                "tab_access": user_data.get('tab_access', 'all')
                            }
                            st.rerun()
                            
                        except Exception as e:
                            logging.error(f"Error fetching user data: {str(e)}")
                            st.error("Error fetching user data. Please contact administrator.")
                            
                    except ValueError as ve:
                        st.error(str(ve))  # Show configuration errors
                    except Exception as e:
                        logging.error(f"Login error: {str(e)}")
                        st.error("Login failed. Please try again later or contact administrator.") 