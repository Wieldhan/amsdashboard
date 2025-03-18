from supabase import create_client
import os
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

@lru_cache()
def get_supabase_client(use_service_role=False):
    """Get cached Supabase client instance
    
    Args:
        use_service_role (bool): If True, uses the service role key instead of anon key
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY" if use_service_role else "SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        
    return create_client(supabase_url, supabase_key)

def get_admin_client():
    """Get a Supabase client with service role privileges"""
    return get_supabase_client(use_service_role=True) 