from supabase import create_client
import os
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path
import streamlit as st

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Function to check for env vars in streamlit secrets as fallback
def get_env_var(var_name, default=None):
    # First try OS environment variables (loaded from .env)
    value = os.environ.get(var_name)
    
    # If not found, check Streamlit secrets
    if not value:
        # For Supabase section
        if var_name.startswith("SUPABASE_"):
            key = var_name[9:].lower()  # Remove SUPABASE_ prefix and lowercase
            if "supabase" in st.secrets and key in st.secrets["supabase"]:
                value = st.secrets["supabase"][key]
    
    return value or default

@lru_cache()
def get_supabase_client(use_service_role=False):
    """Get cached Supabase client instance
    
    Args:
        use_service_role (bool): If True, uses the service role key instead of anon key
    """
    supabase_url = get_env_var("SUPABASE_URL")
    supabase_key = get_env_var("SUPABASE_SERVICE_ROLE_KEY" if use_service_role else "SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY must be set in .env file or Streamlit secrets")
        
    return create_client(supabase_url, supabase_key)

def get_admin_client():
    """Get a Supabase client with service role privileges"""
    return get_supabase_client(use_service_role=True) 