import pandas as pd
import streamlit as st
from src.backend.database_utils import (
    handle_db_errors,
    get_cached_data,
    validate_lending_data
)

@st.cache_data(ttl=3600)
@handle_db_errors(default_return=lambda: (pd.DataFrame(), pd.DataFrame()))
def get_lending_data(start_date, end_date):
    """Get lending data from Supabase within date range"""
    with st.spinner('Loading financing data...'):
        # Define columns for pembiayaan
        pembiayaan_columns = [
            'tanggal', 'kode_cabang', 'kode_produk', 'kolektibilitas',
            'jml_pencairan', 'byr_pokok', 'outstanding', 'kd_sts_pemb',
            'kode_grup1', 'kode_grup2', 'kd_kolektor'
        ]
        
        # Get pembiayaan data
        pembiayaan_df = get_cached_data('pembiayaan_data', start_date, end_date, pembiayaan_columns)
        
    with st.spinner('Loading rahn data...'):
        # Define columns for rahn
        rahn_columns = ['tanggal', 'kode_cabang', 'kode_produk', 'nominal', 'kolektibilitas']
        
        # Get rahn data
        rahn_df = get_cached_data('rahn_data', start_date, end_date, rahn_columns)
    
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
        pembiayaan_df = pembiayaan_df.rename(columns=pembiayaan_mapping)
        pembiayaan_df = validate_lending_data(pembiayaan_df)
        
    if not rahn_df.empty:
        rahn_df = rahn_df.rename(columns=rahn_mapping)
        rahn_df = validate_lending_data(rahn_df)
        
    return pembiayaan_df, rahn_df