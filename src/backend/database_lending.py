import pandas as pd
import streamlit as st
from src.backend.database_utils import (
    handle_db_errors,
    get_cached_data,
    validate_lending_data
)
from src.backend.supabase_client import get_supabase_client, get_admin_client

@st.cache_data(ttl=3600)
@handle_db_errors(default_return=lambda: (pd.DataFrame(), pd.DataFrame()))
def get_lending_data(start_date, end_date):
    """Get lending data from Supabase within date range"""
    # Define columns to fetch
    pembiayaan_columns = [
        'tanggal', 'kode_cabang', 'kode_produk', 'kolektibilitas',
        'jml_pencairan', 'byr_pokok', 'outstanding', 'kd_sts_pemb',
        'kode_grup1', 'kode_grup2', 'kd_kolektor'
    ]
    
    rahn_columns = ['tanggal', 'kode_cabang', 'kode_produk', 'nominal', 'kolektibilitas']
    
    print(f"Fetching lending data from {start_date} to {end_date}")
    
    # Get data for both types using batching method
    pembiayaan_df = get_cached_data('pembiayaan_data', start_date, end_date, pembiayaan_columns)
    rahn_df = get_cached_data('rahn_data', start_date, end_date, rahn_columns)
    
    # Debug information
    if pembiayaan_df.empty:
        print("WARNING: No pembiayaan data fetched")
    else:
        print(f"Fetched {len(pembiayaan_df)} pembiayaan records")
        print(f"Pembiayaan columns: {pembiayaan_df.columns.tolist()}")
        # Check if outstanding column exists
        if 'outstanding' not in pembiayaan_df.columns:
            print("ERROR: 'outstanding' column not found in pembiayaan data!")
            # Try to find similar column names that might contain the outstanding value
            possible_columns = [col for col in pembiayaan_df.columns if 'outstand' in col.lower()]
            print(f"Possible alternative columns: {possible_columns}")
        else:
            # Check for null values
            null_count = pembiayaan_df['outstanding'].isna().sum()
            print(f"Null values in 'outstanding' column: {null_count} out of {len(pembiayaan_df)}")
            
            # Show some sample data
            if not pembiayaan_df.empty:
                print("Sample pembiayaan data:")
                print(pembiayaan_df.head(2))
    
    if rahn_df.empty:
        print("WARNING: No rahn data fetched")
    else:
        print(f"Fetched {len(rahn_df)} rahn records")
        print(f"Rahn columns: {rahn_df.columns.tolist()}")
    
    # Rename columns to match existing code
    pembiayaan_mapping = {
        'tanggal': 'Tanggal',
        'kode_cabang': 'KodeCabang',
        'kode_produk': 'KodeProduk',
        'kolektibilitas': 'Kolektibilitas',
        'jml_pencairan': 'JmlPencairan',
        'byr_pokok': 'ByrPokok',
        'outstanding': 'Outstanding',
        'kd_sts_pemb': 'KdStsPemb',
        'kode_grup1': 'KodeGrup1',
        'kode_grup2': 'KodeGrup2',
        'kd_kolektor': 'KdKolektor'
    }
    
    rahn_mapping = {
        'tanggal': 'Tanggal',
        'kode_cabang': 'KodeCabang',
        'kode_produk': 'KodeProduk',
        'nominal': 'Nominal',
        'kolektibilitas': 'Kolektibilitas'
    }
    
    if not pembiayaan_df.empty:
        # Convert outstanding to numeric, replacing any errors with 0
        if 'outstanding' in pembiayaan_df.columns:
            pembiayaan_df['outstanding'] = pd.to_numeric(pembiayaan_df['outstanding'], errors='coerce').fillna(0)
        
        pembiayaan_df = pembiayaan_df.rename(columns=pembiayaan_mapping)
        pembiayaan_df = validate_lending_data(pembiayaan_df)
        
        # After validation, check if Outstanding column exists and has valid data
        if 'Outstanding' in pembiayaan_df.columns:
            # Print statistics about the Outstanding column
            print(f"Pembiayaan Outstanding min: {pembiayaan_df['Outstanding'].min()}, max: {pembiayaan_df['Outstanding'].max()}, mean: {pembiayaan_df['Outstanding'].mean()}")
        
    if not rahn_df.empty:
        # Convert nominal to numeric
        if 'nominal' in rahn_df.columns:
            rahn_df['nominal'] = pd.to_numeric(rahn_df['nominal'], errors='coerce').fillna(0)
            
        rahn_df = rahn_df.rename(columns=rahn_mapping)
        rahn_df = validate_lending_data(rahn_df)
        
        # After validation, check if Nominal column exists and has valid data
        if 'Nominal' in rahn_df.columns:
            print(f"Rahn Nominal min: {rahn_df['Nominal'].min()}, max: {rahn_df['Nominal'].max()}, mean: {rahn_df['Nominal'].mean()}")
        
    return pembiayaan_df, rahn_df