import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st


# Set end date and calculate start date (2 years before)
start_date = pd.Timestamp('2020-01-01')
end_date = pd.Timestamp('2021-07-31')  # Hardcoded for dummy database

# Reuse the same engine creation and management functions
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
    return create_engine(connection_string)

_engine = None

def get_engine():
    
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine

def delete_financing_tables():
    """Delete all tables in financing.db"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/financing.db')
        with sqlite_engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            
            # Drop each table
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"Deleted table: {table}")
                
        print("Successfully deleted all tables from financing.db")
        return True
    except Exception as e:
        print(f"Error deleting financing tables: {str(e)}")
        return False

def create_sqlite_financing_tables(suffix):
    sqlite_engine = create_engine('sqlite:///./database/financing.db')
    
    # Create FinancingData table with suffix
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS FinancingData{suffix} (
        Tanggal DATE,
        KodeCabang VARCHAR(2),
        KodeProduk VARCHAR(50),
        Kolektibilitas INT,
        JmlPencairan DECIMAL(18,2),
        ByrPokok DECIMAL(18,2),
        Outstanding DECIMAL(18,2),
        KdStsPemb VARCHAR(2),
        KodeGrup1 VARCHAR(10),
        KodeGrup2 VARCHAR(10),
        KdKolektor VARCHAR(4),

        PRIMARY KEY (Tanggal, KodeCabang, KodeProduk, Kolektibilitas, KdStsPemb, KodeGrup1, KodeGrup2, KdKolektor)
    )
    """

    
    with sqlite_engine.connect() as conn:
        conn.execute(text(create_table_query))
        
    return sqlite_engine

#@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_financing_balance_data(start_date, end_date):
    
    try:
        engine = get_engine()
        min_date_suffix = start_date.strftime('%Y%m')
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
                    "pattern": 'AMSPinjamanArsip%',
                    "min_date": min_date_suffix,
                    "max_date": max_date_suffix
                }
            )]
            
        if not databases:
            print("No databases found.")
            return None

        all_data = []
        
        balance_query = """
            SELECT 
                ThnBlnTgl as Tanggal,
                LEFT(KodeCabang, 2) as KodeCabang,
                KodeProduk,
                Koll as Kolektibilitas,
                JmlPencairan,
                ByrPokok,
                KdStsPemb,
                KodeGrup1,
                KodeGrup2,
                KdKolektor,
                JmlPencairan - ByrPokok as Outstanding
            FROM {db}.dbo.LnDCORekNominatif{suffix}
            WHERE ThnBlnTgl BETWEEN :start_date AND :end_date
            ORDER BY ThnBlnTgl, KodeCabang, KodeProduk
        """

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
                
                # Group the data
                grouped_df = df.groupby(
                    ['Tanggal', 'KodeCabang', 'KodeProduk', 'Kolektibilitas', 'KdStsPemb', 'KodeGrup1', 'KodeGrup2', 'KdKolektor']
                ).agg({
                    'JmlPencairan': 'sum',
                    'ByrPokok': 'sum',
                    'Outstanding': 'sum'
                }).reset_index()

                
                # Store in SQLite with suffixed table name
                sqlite_engine = create_sqlite_financing_tables(suffix)
                grouped_df.to_sql(f'FinancingData{suffix}', sqlite_engine, if_exists='replace', index=False)
                
                all_data.append(grouped_df)
                print(f"Successfully processed and stored financing data from {db}")
            except Exception as e:
                print(f"Error processing {db}: {str(e)}")
                continue

        if not all_data:
            return None

        return pd.concat(all_data, ignore_index=True)

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def delete_rahn_tables():
    """Delete all tables in rahn.db"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/rahn.db')
        with sqlite_engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            
            # Drop each table
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"Deleted table: {table}")
                
        print("Successfully deleted all tables from rahn.db")
        return True
    except Exception as e:
        print(f"Error deleting rahn tables: {str(e)}")
        return False

    
def create_sqlite_rahn_tables(suffix):
    sqlite_engine = create_engine('sqlite:///./database/rahn.db')
    
    # Create RahnData table with suffix
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS RahnData{suffix} (
        Tanggal DATE,
        KodeCabang VARCHAR(2),
        KodeProduk VARCHAR(50),
        Nominal DECIMAL(18,2),
        Kolektibilitas INT,
        PRIMARY KEY (Tanggal, KodeCabang, KodeProduk, Kolektibilitas)
    )
    """
    
    with sqlite_engine.connect() as conn:
        conn.execute(text(create_table_query))
        
    return sqlite_engine

#@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_rahn_balance_data(start_date, end_date):
   
    try:
        engine = get_engine()

        min_date_suffix = start_date.strftime('%Y%m')  # Format as YYYYMM
        max_date_suffix = end_date.strftime('%Y%m')

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
                    "pattern": 'AMSRahnArsip%',
                    "min_date": min_date_suffix,
                    "max_date": max_date_suffix
                }
            )]

        all_data = []
        
        balance_query = """
            SELECT 
                ThnBlnTgl as Tanggal,
                LEFT(KodeCabang, 2) as KodeCabang,
                KodeProduk,
                JmlPinjaman as Nominal,
                Koll as Kolektibilitas
            FROM {db}.dbo.RHDCORekNominatif{suffix}
            WHERE ThnBlnTgl BETWEEN :start_date AND :end_date
            ORDER BY ThnBlnTgl, KodeCabang, KodeProduk
        """

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
                
                # Add grouping operation
                grouped_df = df.groupby(
                    ['Tanggal', 'KodeCabang', 'KodeProduk', 'Kolektibilitas']
                ).agg({
                    'Nominal': 'sum'
                }).reset_index()
                
                # Store grouped data in SQLite
                sqlite_engine = create_sqlite_rahn_tables(suffix)
                grouped_df.to_sql(f'RahnData{suffix}', sqlite_engine, if_exists='replace', index=False)
                
                all_data.append(grouped_df)
                print(f"Successfully processed and stored rahn data from {db}")
            except Exception as e:
                print(f"Error processing {db}: {str(e)}")
                continue

        if not all_data:
            return None

        return pd.concat(all_data, ignore_index=True)

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_financing_data_from_sqlite(start_date, end_date):
    """Retrieve financing data from SQLite database for given date range"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/financing.db')
        min_date_suffix = start_date.strftime('%Y%m')
        max_date_suffix = end_date.strftime('%Y%m')
        
        all_data = []
        with sqlite_engine.connect() as conn:
            # Get all table names
            tables = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'FinancingData%'"
            )).fetchall()
            
            for (table_name,) in tables:
                suffix = table_name[-6:]  # Extract YYYYMM suffix
                if min_date_suffix <= suffix <= max_date_suffix:
                    query = text(f"SELECT * FROM {table_name}")
                    df = pd.read_sql_query(query, conn)
                    all_data.append(df)
                    print(f"Successfully get financing data from {table_name}")
        
        return pd.concat(all_data, ignore_index=True) if all_data else None
    
    except Exception as e:
        print(f"Error retrieving financing data from SQLite: {str(e)}")
        return None

def get_rahn_data_from_sqlite(start_date, end_date):
    """Retrieve rahn data from SQLite database for given date range"""
    try:
        sqlite_engine = create_engine('sqlite:///./database/rahn.db')
        min_date_suffix = start_date.strftime('%Y%m')
        max_date_suffix = end_date.strftime('%Y%m')
        
        all_data = []
        with sqlite_engine.connect() as conn:
            # Get all table names
            tables = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'RahnData%'"
            )).fetchall()
            
            for (table_name,) in tables:
                suffix = table_name[-6:]  # Extract YYYYMM suffix
                if min_date_suffix <= suffix <= max_date_suffix:
                    query = text(f"SELECT * FROM {table_name}")
                    df = pd.read_sql_query(query, conn)
                    all_data.append(df)
                    print(f"Successfully get rahn data from {table_name}")
        
        return pd.concat(all_data, ignore_index=True) if all_data else None
    
    except Exception as e:
        print(f"Error retrieving rahn data from SQLite: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_lending_data(start_date, end_date):
    with st.spinner('Loading financing data...'):
        financing_data = get_financing_data_from_sqlite(start_date, end_date)
    with st.spinner('Loading rahn data...'):
        rahn_data = get_rahn_data_from_sqlite(start_date, end_date)
    return financing_data, rahn_data