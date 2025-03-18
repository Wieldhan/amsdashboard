import streamlit as st
import os
from src.backend.supabase_client import get_supabase_client, get_admin_client

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_funding_product_mapping():
    """Get funding product mappings from Supabase"""
    try:
        # Use admin client to bypass authentication restrictions
        supabase = get_admin_client()
        
        # Get deposito products
        deposito_response = supabase.table('deposito_product_mapping') \
                                  .select('kode_produk, nama_produk') \
                                  .execute()
        
        # Get tabungan products
        tabungan_response = supabase.table('tabungan_product_mapping') \
                                  .select('kode_produk, nama_produk') \
                                  .execute()
        
        deposito_products = {row['kode_produk']: row['nama_produk'] or f"Deposito {row['kode_produk']}"
                           for row in deposito_response.data} if deposito_response.data else {}
        
        tabungan_products = {row['kode_produk']: row['nama_produk'] or f"Tabungan {row['kode_produk']}"
                           for row in tabungan_response.data} if tabungan_response.data else {}
            
        return deposito_products, tabungan_products
        
    except Exception as e:
        print(f"Error fetching funding product mappings: {str(e)}")
        return {}, {}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_lending_product_mapping():
    """Get lending product mappings from Supabase"""
    try:
        # Use admin client to bypass authentication restrictions
        supabase = get_admin_client()
        
        # Get pembiayaan products
        pembiayaan_response = supabase.table('pembiayaan_product_mapping') \
                                    .select('kode_produk, nama_produk') \
                                    .execute()
        
        # Get rahn products
        rahn_response = supabase.table('rahn_product_mapping') \
                               .select('kode_produk, nama_produk') \
                               .execute()
        
        pembiayaan_products = {row['kode_produk']: row['nama_produk'] or f"Pembiayaan {row['kode_produk']}"
                             for row in pembiayaan_response.data} if pembiayaan_response.data else {}
        
        rahn_products = {row['kode_produk']: row['nama_produk'] or f"Rahn {row['kode_produk']}"
                        for row in rahn_response.data} if rahn_response.data else {}
        
        return pembiayaan_products, rahn_products
        
    except Exception as e:
        print(f"Error fetching lending product mappings: {str(e)}")
        return {}, {}

if __name__ == "__main__":
    print(get_lending_product_mapping())
    print(get_funding_product_mapping())