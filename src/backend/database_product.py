from sqlalchemy import text
import streamlit as st
from backend.database_funding import get_engine

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_funding_product_mapping():

    try:
        engine = get_engine()
        
        # Get savings product mapping
        saving_query = text("""
            SELECT KodeProduk, NamaProduk 
            FROM AMSRekening.dbo.RekProdukPR
        """)
        
        # Get deposito product mapping
        deposito_query = text("""
            SELECT KodeProduk, NamaProduk 
            FROM AMSDeposito.dbo.DepositoProdukPR
        """)
        
        with engine.connect() as conn:
            saving_products = {row[0]: row[1] for row in conn.execute(saving_query)}
            deposito_products = {row[0]: row[1] for row in conn.execute(deposito_query)}
            
        return deposito_products, saving_products
        
    except Exception as e:
        print(f"Error fetching funding product mappings: {str(e)}")
        return {}, {}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_lending_product_mapping():

    try:
        engine = get_engine()
        
        # Get financing product mapping with UPPER() function
        financing_query = text("""
            SELECT KodeProduk, UPPER(NamaProduk) as NamaProduk 
            FROM AMSPinjaman.dbo.LnProduk
            WHERE StatusProduk = 1
        """)
        
        # Get rahn product mapping with UPPER() function
        rahn_query = text("""
            SELECT KdPrdk as KodeProduk, UPPER(NamaProduk) as NamaProduk 
            FROM AMSRahn.dbo.RAHN_Produk
            WHERE StsPrdk = 'AKTIF'
        """)
        
        with engine.connect() as conn:
            financing_products = {row[0]: row[1] for row in conn.execute(financing_query)}
            rahn_products = {row[0]: row[1] for row in conn.execute(rahn_query)}
            
        return financing_products, rahn_products
        
    except Exception as e:
        print(f"Error fetching lending product mappings: {str(e)}")
        return {}, {} 
    
if __name__ == "__main__":
    print(get_lending_product_mapping())
    print(get_funding_product_mapping())