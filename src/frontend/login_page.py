import streamlit as st
from src.backend.user_management import UserManagement

def login_page():
    # Initialize user management
    user_mgmt = UserManagement()
    
    # Create three columns with the middle one having a fixed width
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Container for login form
        with st.container():
            # Center the logo and limit its size
            col1_img, col2_img, col3_img = st.columns([1, 2, 1])
            with col2_img:
                st.image("logo.png")  # Adjust width as needed
            
            # Title with custom CSS for centering
            st.markdown("<h1 style='text-align: center;'>AMS Dashboard Login</h1>", unsafe_allow_html=True)
            
            # Add some spacing
            st.write("")
            
            # Login form with custom styling
            with st.form("login_form"):
                # Add a light background and padding
                user_id = st.text_input("User ID")
                password = st.text_input("Password", type="password")
                
                # Center the login button and make it more prominent
                col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])
                with col2_btn:
                    submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if user_mgmt.verify_password(user_id, password):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.user_access = user_mgmt.get_user_access(user_id)
                        st.rerun()
                    else:
                        st.error("ID & Password tidak ditemukan") 