import streamlit as st
from src.backend.supabase_client import get_supabase_client

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_branch_mapping():
    """Get branch mapping from Supabase"""
    try:
        supabase = get_supabase_client()
        response = supabase.table('branch_mapping') \
                          .select('kode_cabang, nama_cabang') \
                          .execute()
        
        return {row['kode_cabang']: row['nama_cabang'] 
                for row in response.data} if response.data else {}
                
    except Exception as e:
        print(f"Error fetching branch mappings: {str(e)}")
        return {}

if __name__ == "__main__":
    print(get_branch_mapping())

