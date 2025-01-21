import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st
    
def create_db_engine():
    server = '10.10.10.105,1344'
    username = 'sa'
    password = 'sa'
    database = 'master'
    driver = 'ODBC Driver 17 for SQL Server'

    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?"
        f"driver={driver}&Encrypt=no&TrustServerCertificate=yes"
    )

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine

def delete_deposito_tables():
    """Delete all tables in deposito.db"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/deposito.db')
        with sqlite_engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            
            # Drop each table
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"Deleted table: {table}")
                
        print("Successfully deleted all tables from deposito.db")
        return True
    except Exception as e:
        print(f"Error deleting funding tables: {str(e)}")
        return False

def delete_saving_tables():
    """Delete all tables in saving.db"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/saving.db')
        with sqlite_engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            
            # Drop each table
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"Deleted table: {table}")
                
        print("Successfully deleted all tables from saving.db")
        return True
    except Exception as e:
        print(f"Error deleting saving tables: {str(e)}")
        return False

def create_sqlite_deposito_tables(suffix):
    sqlite_engine = create_engine('sqlite:///./database/deposito.db')
    
    # Create DepositoData table with suffix
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS DepositoData{suffix} (
        Tanggal DATE,
        KodeCabang VARCHAR(2),
        KodeProduk VARCHAR(50),
        Nominal DECIMAL(18,2),
        PRIMARY KEY (Tanggal, KodeCabang, KodeProduk)
    )
    """
    
    with sqlite_engine.connect() as conn:
        conn.execute(text(create_table_query))
        
    return sqlite_engine

def create_sqlite_saving_tables(suffix):
    sqlite_engine = create_engine('sqlite:///./database/saving.db')
    
    # Create SavingData table with suffix
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS SavingData{suffix} (
        Tanggal DATE,
        KodeCabang VARCHAR(2),
        KodeProduk VARCHAR(50),
        Nominal DECIMAL(18,2),
        PRIMARY KEY (Tanggal, KodeCabang, KodeProduk)
    )
    """
    
    with sqlite_engine.connect() as conn:
        conn.execute(text(create_table_query))
        
    return sqlite_engine

def get_deposito_balance_data(start_date, end_date):
    try:
        engine = get_engine()
        min_date_suffix = start_date.strftime('%Y%m')  # Format as YYYYMM
        max_date_suffix = end_date.strftime('%Y%m')

        # Get list of relevant databases
        query_databases = text("""
        SELECT name 
        FROM sys.databases 
        WHERE name LIKE :pattern
        AND RIGHT(name, 6) >= :min_date
        AND RIGHT(name, 6) <= :max_date
        ORDER BY name
        """)
        
        with engine.connect() as conn:
            databases = [row[0] for row in conn.execute(
                query_databases, 
                {
                    "pattern": 'AMSDepositoArsip%',
                    "min_date": min_date_suffix,
                    "max_date": max_date_suffix
                }
            )]

        if not databases:
            print("No databases found.")
            return None

        # Initialize list for dataframes
        balance_dataframes = []

        # Define the query template for DepSldPrdk
        balance_query = """
            SELECT 
                Tanggal,
                KodeCabang,
                KodeProduk,
                Nominal
            FROM {db}.dbo.DepSldPrdk{suffix}
            WHERE Tanggal BETWEEN :start_date AND :end_date
            ORDER BY Tanggal, KodeCabang, KodeProduk
        """

        # Process each database
        for db in databases:
            suffix = db[-6:]  # Extract YYYYMM from database name
            
            try:
                query = text(balance_query.format(db=db, suffix=suffix))
                df = pd.read_sql_query(
                    query, 
                    engine,
                    params={
                        "start_date": start_date,
                        "end_date": end_date
                    }
                )
                
                # Store in SQLite with suffixed table name
                sqlite_engine = create_sqlite_deposito_tables(suffix)
                df.to_sql(f'DepositoData{suffix}', sqlite_engine, if_exists='replace', index=False)
                
                balance_dataframes.append(df)
                print(f"Successfully processed and stored deposito data from {db}")
            except Exception as e:
                print(f"Error processing {db}: {str(e)}")
                continue

        if not balance_dataframes:
            return None

        return pd.concat(balance_dataframes, ignore_index=True)

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_savings_balance_data(start_date, end_date):
    try:
        engine = get_engine()
        min_date_suffix = start_date.strftime('%Y%m')  # Format as YYYYMM
        max_date_suffix = end_date.strftime('%Y%m')

        # Get list of relevant databases
        query_databases = text("""
        SELECT name 
        FROM sys.databases 
        WHERE name LIKE :pattern
        AND RIGHT(name, 6) >= :min_date
        AND RIGHT(name, 6) <= :max_date
        ORDER BY name
        """)
        
        with engine.connect() as conn:
            databases = [row[0] for row in conn.execute(
                query_databases, 
                {
                    "pattern": 'AMSRekeningArsip%',
                    "min_date": min_date_suffix,
                    "max_date": max_date_suffix
                }
            )]

        if not databases:
            print("No savings databases found.")
            return None

        # Initialize list for dataframes
        balance_dataframes = []

        # Define the query template for RekSldPrdk
        balance_query = """
            SELECT 
                Tanggal,
                KodeCabang,
                KodeProduk,
                Nominal
            FROM {db}.dbo.RekSldPrdk{suffix}
            WHERE Tanggal BETWEEN :start_date AND :end_date
            ORDER BY Tanggal, KodeCabang, KodeProduk
        """

        # Process each database
        for db in databases:
            suffix = db[-6:]
            try:
                query = text(balance_query.format(db=db, suffix=suffix))
                df = pd.read_sql_query(
                    query, 
                    engine,
                    params={
                        "start_date": start_date,
                        "end_date": end_date
                    }
                )
                
                # Store in SQLite with suffixed table name
                sqlite_engine = create_sqlite_saving_tables(suffix)
                df.to_sql(f'SavingData{suffix}', sqlite_engine, if_exists='replace', index=False)
                
                balance_dataframes.append(df)
                print(f"Successfully processed and stored savings data from {db}")
            except Exception as e:
                print(f"Error processing {db}: {str(e)}")
                continue

        if not balance_dataframes:
            return None

        return pd.concat(balance_dataframes, ignore_index=True)

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_deposito_data_from_sqlite(start_date, end_date):
    """Retrieve deposito data from SQLite database for given date range"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/deposito.db')
        min_date_suffix = start_date.strftime('%Y%m')
        max_date_suffix = end_date.strftime('%Y%m')
        
        all_data = []
        with sqlite_engine.connect() as conn:
            # Get all table names
            tables = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'DepositoData%'"
            )).fetchall()
            
            for (table_name,) in tables:
                suffix = table_name[-6:]  # Extract YYYYMM suffix
                if min_date_suffix <= suffix <= max_date_suffix:
                    query = text(f"SELECT * FROM {table_name}")
                    df = pd.read_sql_query(query, conn)
                    all_data.append(df)
                    print(f"Successfully get deposito data from {table_name}")
        
        return pd.concat(all_data, ignore_index=True) if all_data else None
    
    except Exception as e:
        print(f"Error retrieving deposito data from SQLite: {str(e)}")
        return None

def get_saving_data_from_sqlite(start_date, end_date):
    """Retrieve saving data from SQLite database for given date range"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/saving.db')
        min_date_suffix = start_date.strftime('%Y%m')
        max_date_suffix = end_date.strftime('%Y%m')
        
        all_data = []
        with sqlite_engine.connect() as conn:
            # Get all table names
            tables = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'SavingData%'"
            )).fetchall()
            
            for (table_name,) in tables:
                suffix = table_name[-6:]  # Extract YYYYMM suffix
                if min_date_suffix <= suffix <= max_date_suffix:
                    query = text(f"SELECT * FROM {table_name}")
                    df = pd.read_sql_query(query, conn)
                    all_data.append(df)
                    print(f"Successfully get saving data from {table_name}")
        
        return pd.concat(all_data, ignore_index=True) if all_data else None
    
    except Exception as e:
        print(f"Error retrieving saving data from SQLite: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_funding_data(start_date, end_date):
    with st.spinner('Loading deposito data...'):
        deposito_data = get_deposito_data_from_sqlite(start_date, end_date)
    with st.spinner('Loading savings data...'):
        saving_data = get_saving_data_from_sqlite(start_date, end_date)
    return deposito_data, saving_data
