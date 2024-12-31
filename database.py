import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

def create_db_engine():
    server = '10.10.10.105,1344'
    username = 'sa'
    password = 'sa'
    database = 'master'
    driver = 'ODBC Driver 17 for SQL Server'

    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?"
        f"driver={driver}"
    )

    return create_engine(connection_string)

def fetch_database_names(engine, pattern, min_date):
    query = text(f"""
        SELECT name 
        FROM sys.databases 
        WHERE name LIKE '{pattern}'
        AND RIGHT(name, 6) >= '{min_date}'
        ORDER BY name
    """)

    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query)]

def fetch_balance_data(engine, databases, table_template):
    dataframes = []

    for db in databases:
        suffix = db[-6:]
        query = text(table_template.format(db=db, suffix=suffix))

        try:
            df = pd.read_sql_query(query, engine)
            df['SourceDatabase'] = db
            dataframes.append(df)
            print(f"Successfully retrieved data from {db}")
        except Exception as e:
            print(f"Error processing {db}: {str(e)}")
            continue

    if not dataframes:
        print("No data could be retrieved from any database.")
        return None

    final_df = pd.concat(dataframes, ignore_index=True)
    return final_df

def perform_data_quality_checks(df, value_column):
    print("\n=== Data Quality Checks ===")
    print(f"Total NaN values in each column:")
    print(df.isna().sum())

    print("\nNominal statistics:")
    print(df[value_column].describe())

    neg_values = df[df[value_column] < 0]
    zero_values = df[df[value_column] == 0]

    print(f"\nNegative {value_column} values: {len(neg_values):,}")
    print(f"Zero {value_column} values: {len(zero_values):,}")

    if len(neg_values) > 0:
        print("\nSample of negative values:")
        print(neg_values.head())

def get_product_branch_mappings():
    try:
        engine = create_db_engine()

        queries = {
            'saving_products': "SELECT KodeProduk, NamaProduk FROM AMSRekening.dbo.RekProdukPR",
            'deposito_products': "SELECT KodeProduk, NamaProduk FROM AMSDeposito.dbo.DepositoProdukPR",
            'branches': "SELECT KodeCabang, NamaCabang FROM AMS.dbo.PICabang"
        }

        mappings = {}

        with engine.connect() as conn:
            for key, query in queries.items():
                mappings[key] = {row[0]: row[1] for row in conn.execute(text(query))}

        return mappings
    except Exception as e:
        print(f"Error fetching mappings: {str(e)}")
        return {}

if __name__ == "__main__":
    print("Retrieving product and branch mappings...")
    mappings = get_product_branch_mappings()

    engine = create_db_engine()

    print("\nRetrieving deposit balance data...")
    deposit_databases = fetch_database_names(engine, 'AMSDepositoArsip%', '201301')
    deposit_query = """
        SELECT 
            Tanggal,
            KodeCabang,
            KodeProduk,
            Nominal
        FROM {db}.dbo.DepSldPrdk{suffix}
        ORDER BY Tanggal, KodeCabang, KodeProduk
    """
    df_deposit = fetch_balance_data(engine, deposit_databases, deposit_query)

    if df_deposit is not None:
        perform_data_quality_checks(df_deposit, 'Nominal')

    print("\nRetrieving savings balance data...")
    savings_databases = fetch_database_names(engine, 'AMSRekeningArsip%', '201301')
    savings_query = """
        SELECT 
            Tanggal,
            KodeCabang,
            KodeProduk,
            Nominal
        FROM {db}.dbo.RekSldPrdk{suffix}
        ORDER BY Tanggal, KodeCabang, KodeProduk
    """
    df_savings = fetch_balance_data(engine, savings_databases, savings_query)

    if df_savings is not None:
        perform_data_quality_checks(df_savings, 'Nominal')

    if df_deposit is not None and df_savings is not None:
        print("\nDeposit Data Sample:")
        print(df_deposit.head())

        print("\nSavings Data Sample:")
        print(df_savings.head())

        print("\nTotal balances by product type:")
        print("Deposits:", df_deposit['Nominal'].sum())
        print("Savings:", df_savings['Nominal'].sum())