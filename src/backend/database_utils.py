from functools import wraps
import pandas as pd
import streamlit as st
from src.backend.supabase_client import get_supabase_client

def handle_db_errors(default_return=None):
    """Decorator for handling database errors consistently"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Database error in {func.__name__}: {str(e)}"
                print(error_msg)  # For logging
                st.error(error_msg)  # For UI
                return default_return() if callable(default_return) else default_return
        return wrapper
    return decorator

@st.cache_data(ttl=3600)
def get_all_mappings():
    """Get all mappings in one call to reduce network requests"""
    try:
        supabase = get_supabase_client()
        
        # Execute all requests
        branch_response = supabase.table('branch_mapping').select('kode_cabang, nama_cabang').execute()
        grup1_response = supabase.table('grup1_mapping').select('kode_grup1, nama_grup').execute()
        grup2_response = supabase.table('grup2_mapping').select('kode_grup2, nama_grup').execute()
        
        return {
            'branches': {row['kode_cabang']: row['nama_cabang'] 
                        for row in branch_response.data} if branch_response.data else {},
            'grup1': {row['kode_grup1']: row['nama_grup'] 
                     for row in grup1_response.data} if grup1_response.data else {},
            'grup2': {row['kode_grup2']: row['nama_grup'] 
                     for row in grup2_response.data} if grup2_response.data else {}
        }
    except Exception as e:
        print(f"Error fetching mappings: {str(e)}")
        return {'branches': {}, 'grup1': {}, 'grup2': {}}

def validate_funding_data(df):
    """Validate funding data structure and types"""
    required_columns = ['Tanggal', 'KodeCabang', 'KodeProduk', 'Nominal']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in funding data")
    return df

def validate_lending_data(df):
    """Validate lending data structure and types"""
    required_columns = ['Tanggal', 'KodeCabang', 'KodeProduk']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in lending data")
    return df

def get_data_in_batches(table_name, start_date, end_date, columns, batch_size=30):
    """Get data in batches for large date ranges"""
    try:
        supabase = get_supabase_client()
        all_data = []
        current_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        while current_date <= end_date:
            next_date = min(current_date + pd.Timedelta(days=batch_size), end_date)
            
            # Get batch of data
            response = supabase.table(table_name) \
                .select(','.join(columns)) \
                .gte('tanggal', current_date.strftime('%Y-%m-%d')) \
                .lt('tanggal', next_date.strftime('%Y-%m-%d')) \
                .execute()
                
            if response.data:
                all_data.extend(response.data)
            
            current_date = next_date
            
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()
        
    except Exception as e:
        print(f"Error in batch retrieval for {table_name}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, max_entries=100)
def get_cached_data(table_name, start_date, end_date, columns, granularity='D'):
    """Get cached data with granularity control"""
    # Round dates to reduce cache variations
    start = pd.Timestamp(start_date).floor(granularity)
    end = pd.Timestamp(end_date).ceil(granularity)
    
    # Get data in batches
    df = get_data_in_batches(table_name, start, end, columns)
    
    # Convert tanggal to datetime if data exists
    if not df.empty and 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        
    return df 