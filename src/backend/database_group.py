import streamlit as st
from src.backend.supabase_client import get_supabase_client

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_grup1_mapping():
    """Get group 1 mapping from Supabase"""
    try:
        supabase = get_supabase_client()
        response = supabase.table('grup1_mapping') \
                          .select('kode_grup1, nama_grup') \
                          .execute()
        
        return {row['kode_grup1']: row['nama_grup'] 
                for row in response.data} if response.data else {}
                
    except Exception as e:
        print(f"Error fetching group 1 mappings: {str(e)}")
        return {}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_grup2_mapping():
    """Get group 2 mapping from Supabase"""
    try:
        supabase = get_supabase_client()
        response = supabase.table('grup2_mapping') \
                          .select('kode_grup2, nama_grup') \
                          .execute()
        
        return {row['kode_grup2']: row['nama_grup'] 
                for row in response.data} if response.data else {}
                
    except Exception as e:
        print(f"Error fetching group 2 mappings: {str(e)}")
        return {}

if __name__ == "__main__":
    print(get_grup1_mapping())
    print(get_grup2_mapping())
