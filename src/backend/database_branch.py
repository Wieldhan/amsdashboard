import streamlit as st
from src.backend.supabase_client import get_admin_client

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_branch_mapping():
    """Get branch mapping from Supabase"""
    try:
        supabase = get_admin_client()
        response = supabase.table('branch_mapping') \
                          .select('kode_cabang, nama_cabang') \
                          .execute()
        
        if not response.data:
            st.warning("No branch data found in database")
            print("No branch data found in database")  # For logging
            return {}
            
        return {row['kode_cabang']: row['nama_cabang'] 
                for row in response.data}
                
    except Exception as e:
        error_msg = f"Error fetching branch mappings: {str(e)}"
        st.error(error_msg)
        print(error_msg)  # For logging
        return {}

if __name__ == "__main__":
    print(get_branch_mapping())

