import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

def create_db_engine():
    """
    Creates and returns a database engine with standard credentials.
    """
    server = '10.10.10.105,1344'
    username = 'sa'
    password = 'sa'
    return create_engine(f'mssql+pyodbc://{username}:{password}@{server}/master?driver=SQL+Server')

def get_deposito_balance_data():
    """
    Retrieve daily deposito balance data from AMSDepositoArsip databases starting from 201301
    using the pre-aggregated DepSldPrdk tables.
    
    Returns:
        pandas.DataFrame: Daily balance data containing Tanggal, KodeCabang, KodeProduk, Nominal
    """
    # Database credentials
    server = '10.10.10.105,1344'
    username = 'sa'
    password = 'sa'

    try:
        # Create SQLAlchemy engine
        engine = create_engine(f'mssql+pyodbc://{username}:{password}@{server}/master?driver=SQL+Server')

        # Get list of relevant databases
        query_databases = text("""
        SELECT name 
        FROM sys.databases 
        WHERE name LIKE 'AMSDepositoArsip%'
        AND RIGHT(name, 6) >= '201301'
        ORDER BY name
        """)
        
        with engine.connect() as conn:
            databases = [row[0] for row in conn.execute(query_databases)]

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
            ORDER BY Tanggal, KodeCabang, KodeProduk
        """

        # Process each database
        for db in databases:
            suffix = db[-6:]  # Extract YYYYMM from database name
            
            try:
                query = text(balance_query.format(db=db, suffix=suffix))
                df = pd.read_sql_query(query, engine)
                df['SourceDatabase'] = db
                balance_dataframes.append(df)
                print(f"Successfully retrieved balance data from {db}")
            except Exception as e:
                print(f"Error processing {db}: {str(e)}")
                continue

        # Combine all dataframes
        if not balance_dataframes:
            print("No data could be retrieved from any database.")
            return None

        final_df = pd.concat(balance_dataframes, ignore_index=True)
        
        # Add data quality checks
        print("\n=== Deposito Data Quality Checks ===")
        print(f"Total NaN values in each column:")
        print(final_df.isna().sum())
        
        print("\nNominal statistics:")
        print(final_df['Nominal'].describe())
        
        # Check for negative or zero values
        neg_values = final_df[final_df['Nominal'] < 0]
        zero_values = final_df[final_df['Nominal'] == 0]
        print(f"\nNegative Nominal values: {len(neg_values):,}")
        print(f"Zero Nominal values: {len(zero_values):,}")
        
        if len(neg_values) > 0:
            print("\nSample of negative values:")
            print(neg_values.head())
            
        # Print summary
        print(f"\nTotal daily balance records: {len(final_df):,}")
        print(f"Date range: {final_df['Tanggal'].min()} to {final_df['Tanggal'].max()}")
        print(f"Number of branches: {final_df['KodeCabang'].nunique():,}")
        print(f"Number of products: {final_df['KodeProduk'].nunique():,}")

        return final_df

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_savings_balance_data():
    """
    Retrieve daily savings balance data from AMSRekeningArsip databases starting from 201301
    using the pre-aggregated RekSldPrdk tables.
    
    Returns:
        pandas.DataFrame: Daily balance data containing Tanggal, KodeCabang, KodeProduk, Nominal
    """
    try:
        engine = create_db_engine()

        # Get list of relevant databases
        query_databases = text("""
        SELECT name 
        FROM sys.databases 
        WHERE name LIKE 'AMSRekeningArsip%'
        AND RIGHT(name, 6) >= '201301'
        ORDER BY name
        """)
        
        with engine.connect() as conn:
            databases = [row[0] for row in conn.execute(query_databases)]

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
            ORDER BY Tanggal, KodeCabang, KodeProduk
        """

        # Process each database
        for db in databases:
            suffix = db[-6:]  # Extract YYYYMM from database name
            
            try:
                query = text(balance_query.format(db=db, suffix=suffix))
                df = pd.read_sql_query(query, engine)
                df['SourceDatabase'] = db
                balance_dataframes.append(df)
                print(f"Successfully retrieved savings balance data from {db}")
            except Exception as e:
                print(f"Error processing {db}: {str(e)}")
                continue

        # Combine all dataframes
        if not balance_dataframes:
            print("No savings data could be retrieved from any database.")
            return None

        final_df = pd.concat(balance_dataframes, ignore_index=True)
        
        # Add data quality checks
        print("\n=== Savings Data Quality Checks ===")
        print(f"Total NaN values in each column:")
        print(final_df.isna().sum())
        
        print("\nNominal statistics:")
        print(final_df['Nominal'].describe())
        
        # Check for negative or zero values
        neg_values = final_df[final_df['Nominal'] < 0]
        zero_values = final_df[final_df['Nominal'] == 0]
        print(f"\nNegative Nominal values: {len(neg_values):,}")
        print(f"Zero Nominal values: {len(zero_values):,}")
        
        if len(neg_values) > 0:
            print("\nSample of negative values:")
            print(neg_values.head())
            
        # Print summary
        print(f"\nTotal daily savings balance records: {len(final_df):,}")
        print(f"Date range: {final_df['Tanggal'].min()} to {final_df['Tanggal'].max()}")
        print(f"Number of branches: {final_df['KodeCabang'].nunique():,}")
        print(f"Number of products: {final_df['KodeProduk'].nunique():,}")

        return final_df

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_product_branch_mappings():
    """
    Retrieve product and branch name mappings from respective tables.
    
    Returns:
        tuple: (saving_products, deposito_products, branches) dictionaries
    """
    try:
        engine = create_db_engine()
        
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
        
        # Get branch mapping
        branch_query = text("""
            SELECT KodeCabang, NamaCabang 
            FROM AMS.dbo.PICabang
        """)
        
        with engine.connect() as conn:
            saving_products = {row[0]: row[1] for row in conn.execute(saving_query)}
            deposito_products = {row[0]: row[1] for row in conn.execute(deposito_query)}
            branches = {row[0]: row[1] for row in conn.execute(branch_query)}
            
        return saving_products, deposito_products, branches
        
    except Exception as e:
        print(f"Error fetching mappings: {str(e)}")
        return {}, {}, {}

if __name__ == "__main__":
    # Get mappings first
    print("Retrieving product and branch mappings...")
    saving_products, deposito_products, branches = get_product_branch_mappings()
    
    print("\nSavings Products:")
    for code, name in saving_products.items():
        print(f"{code}: {name}")
        
    print("\nDeposito Products:")
    for code, name in deposito_products.items():
        print(f"{code}: {name}")
        
    print("\nBranches:")
    for code, name in branches.items():
        print(f"{code}: {name}")

    # Get both deposit and savings data
    print("\nRetrieving deposit balance data...")
    df_deposit = get_deposito_balance_data()
    
    print("\nRetrieving savings balance data...")
    df_savings = get_savings_balance_data()
    
    if df_deposit is not None and df_savings is not None:
        print("\nDeposit Data Sample:")
        print(df_deposit.head())
        print("\nSavings Data Sample:")
        print(df_savings.head())
        
        # Display combined statistics
        print("\nTotal balances by product type:")
        print("Deposits:", df_deposit['Nominal'].sum())
        print("Savings:", df_savings['Nominal'].sum())
