import pandas as pd
import streamlit as st
from src.backend.database_utils import (
    handle_db_errors,
    get_cached_data,
    validate_funding_data
)

@st.cache_data(ttl=3600)
@handle_db_errors(default_return=lambda: (pd.DataFrame(), pd.DataFrame()))
def get_funding_data(start_date, end_date):
    """Get funding data from Supabase within date range"""
    # Define columns to fetch
    columns = ['tanggal', 'kode_cabang', 'kode_produk', 'nominal']
    
    # Get data for both types
    deposito_df = get_cached_data('deposito_data', start_date, end_date, columns)
    tabungan_df = get_cached_data('tabungan_data', start_date, end_date, columns)
    
    # Rename columns to match existing code
    column_mapping = {
        'tanggal': 'Tanggal',
        'kode_cabang': 'KodeCabang',
        'kode_produk': 'KodeProduk',
        'nominal': 'Nominal'
    }
    
    if not deposito_df.empty:
        deposito_df = deposito_df.rename(columns=column_mapping)
        deposito_df = validate_funding_data(deposito_df)
        
    if not tabungan_df.empty:
        tabungan_df = tabungan_df.rename(columns=column_mapping)
        tabungan_df = validate_funding_data(tabungan_df)
        
    return deposito_df, tabungan_df 