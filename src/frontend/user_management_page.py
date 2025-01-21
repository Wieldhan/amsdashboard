import streamlit as st
from src.backend.user_management import UserManagement

def user_management_page(all_branch_codes, all_branches):
    st.title("User Management")
    
    # Initialize user management
    user_mgmt = UserManagement()
    
    # Create new user
    with st.expander("Create New User"):
        with st.form("create_user"):
            new_user_id = st.text_input("User ID")
            new_password = st.text_input("Default Password", type="password")
            branch_access = st.multiselect(
                "Branch Access", 
                all_branch_codes,
                format_func=lambda x: all_branches[x],
                key="new_user_branch_access"
            )
            tab_access = st.multiselect("Tab Access", ["funding", "lending"], key="new_user_tab_access")
            
            if st.form_submit_button("Create User"):
                branch_str = ",".join(branch_access) if branch_access else "none"
                tab_str = ",".join(tab_access) if tab_access else "none"
                if user_mgmt.create_user(new_user_id, new_password, branch_str, tab_str):
                    st.success("User created successfully")
                else:
                    st.error("Failed to create user")
    
    # List and manage users
    st.subheader("Existing Users")
    users = user_mgmt.get_all_users()
    for user in users:
        if user["user_id"] != "admin":  # Skip admin in the list
            with st.expander(f"User: {user['user_id']}"):
                # Password change section
                with st.form(key=f"password_form_{user['user_id']}"):
                    st.subheader("Change Password")
                    new_password = st.text_input("New Password", type="password", key=f"new_pass_{user['user_id']}")
                    confirm_password = st.text_input("Confirm Password", type="password", key=f"confirm_pass_{user['user_id']}")
                    
                    if st.form_submit_button("Update Password"):
                        if new_password != confirm_password:
                            st.error("Passwords don't match")
                        elif user_mgmt.admin_change_password(user["user_id"], new_password):
                            st.success("Password updated successfully")
                        else:
                            st.error("Failed to update password")
                
                # Access management section
                stored_branch_access = user["branch_access"].split(",")
                valid_branch_access = [b for b in stored_branch_access if b in all_branch_codes]
                
                branch_access = st.multiselect(
                    "Branch Access",
                    all_branch_codes,
                    default=valid_branch_access,
                    format_func=lambda x: all_branches[x],
                    key=f"branch_{user['user_id']}"
                )
                
                new_tab_access = st.multiselect(
                    "Tab Access",
                    ["funding", "lending"],
                    default=user["tab_access"].split(","),
                    key=f"tab_{user['user_id']}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Access", key=f"update_{user['user_id']}"):
                        branch_str = ",".join(branch_access)
                        tab_str = ",".join(new_tab_access)
                        if user_mgmt.update_user_access(user["user_id"], branch_str, tab_str):
                            st.success("Access updated")
                        else:
                            st.error("Failed to update access")
                
                with col2:
                    if st.button("Delete User", key=f"delete_{user['user_id']}"):
                        if user_mgmt.delete_user(user["user_id"]):
                            st.success("User deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete user") 