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
        missing_cols = [col for col in required_columns if col not in df.columns]
        print(f"ERROR: Missing required columns in lending data: {missing_cols}")
        raise ValueError(f"Missing required columns in lending data: {missing_cols}")
    
    # Check for additional expected columns based on data type
    if 'Outstanding' in df.columns:
        # This is pembiayaan data, ensure Outstanding is numeric
        df['Outstanding'] = pd.to_numeric(df['Outstanding'], errors='coerce').fillna(0)
        print(f"Validated Outstanding column in pembiayaan data")
    elif 'Nominal' in df.columns:
        # This is rahn data, ensure Nominal is numeric
        df['Nominal'] = pd.to_numeric(df['Nominal'], errors='coerce').fillna(0)
        print(f"Validated Nominal column in rahn data")
    
    # Ensure Tanggal is datetime
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        # Remove any rows with invalid dates
        invalid_dates = df['Tanggal'].isna().sum()
        if invalid_dates > 0:
            print(f"WARNING: Removed {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=['Tanggal'])
    
    # Ensure KodeCabang and KodeProduk are strings
    if 'KodeCabang' in df.columns:
        df['KodeCabang'] = df['KodeCabang'].astype(str)
    
    if 'KodeProduk' in df.columns:
        df['KodeProduk'] = df['KodeProduk'].astype(str)
    
    return df

def get_data_in_batches(table_name, start_date, end_date, columns, batch_size=30):
    """Get data in batches for large date ranges"""
    try:
        supabase = get_supabase_client(use_service_role=True)  # Use service role for data access
        all_data = []
        current_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        print(f"Fetching {table_name} from {current_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # First, check if the table exists and verify columns
        try:
            # Get a small sample to check structure
            sample_query = supabase.table(table_name).select(','.join(columns)).limit(1)
            sample_response = sample_query.execute()
            
            if sample_response.data:
                print(f"Table {table_name} exists with columns: {list(sample_response.data[0].keys())}")
                # Check if all requested columns exist
                missing_columns = [col for col in columns if col not in sample_response.data[0]]
                if missing_columns:
                    print(f"WARNING: Columns {missing_columns} not found in {table_name}")
            else:
                print(f"Table {table_name} exists but is empty or columns don't match")
                
        except Exception as e:
            print(f"Error checking table structure for {table_name}: {str(e)}")
            if "does not exist" in str(e).lower():
                print(f"ERROR: Table {table_name} does not exist!")
                return pd.DataFrame()
        
        while current_date <= end_date:
            next_date = min(current_date + pd.Timedelta(days=batch_size), end_date + pd.Timedelta(days=1))
            
            # Debug print
            print(f"Batch: {current_date.strftime('%Y-%m-%d')} to {next_date.strftime('%Y-%m-%d')}")
            
            try:
                # Get batch of data - use >= and < operators for clearer date range
                query = supabase.table(table_name) \
                    .select(','.join(columns)) \
                    .gte('tanggal', current_date.strftime('%Y-%m-%d')) \
                    .lt('tanggal', next_date.strftime('%Y-%m-%d'))
                    
                # Execute query and get data
                response = query.execute()
                
                if response.data:
                    print(f"Found {len(response.data)} records")
                    all_data.extend(response.data)
                else:
                    print(f"No data found for this batch")
            except Exception as batch_error:
                print(f"Error fetching batch {current_date.strftime('%Y-%m-%d')} to {next_date.strftime('%Y-%m-%d')}: {str(batch_error)}")
                # Continue to next batch instead of failing completely
            
            current_date = next_date
            
        if not all_data:
            print(f"WARNING: No data found in {table_name} for the entire date range")
            return pd.DataFrame()
        
        # Create DataFrame from collected data
        df = pd.DataFrame(all_data)
        
        # Check data types and try to convert numeric columns
        for col in df.columns:
            try:
                # If column name suggests it's numeric and contains string values, try to convert
                if any(hint in col.lower() for hint in ['outstanding', 'nominal', 'jml', 'pencairan', 'pokok']):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    print(f"Converted {col} to numeric")
            except Exception as e:
                print(f"Could not convert {col} to numeric: {str(e)}")
                
        return df
        
    except Exception as e:
        print(f"ERROR in batch retrieval for {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

@st.cache_data(ttl=3600, max_entries=100)
def get_cached_data(table_name, start_date, end_date, columns, granularity='D'):
    """Get cached data with granularity control"""
    try:
        # Round dates to reduce cache variations
        start = pd.Timestamp(start_date).floor(granularity)
        end = pd.Timestamp(end_date).ceil(granularity)
        
        print(f"Fetching cached data for {table_name} from {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
        
        # Get data in batches
        df = get_data_in_batches(table_name, start, end, columns)
        
        # Convert tanggal to datetime if data exists
        if not df.empty and 'tanggal' in df.columns:
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            
        return df
    except Exception as e:
        print(f"Error in get_cached_data for {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame() 