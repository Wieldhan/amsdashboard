from sqlalchemy import text, create_engine

def create_db_engine():
    server = '10.10.10.105:1344'
    username = 'sa'
    password = 'sa'
    database = 'master'
    driver = 'ODBC Driver 17 for SQL Server'

    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?"
        f"driver={driver}&Encrypt=no&TrustServerCertificate=no"
    )
    return create_engine(connection_string)

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine

def check_data_server():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        print(f"Error checking data server: {e}")
        return False

if __name__ == "__main__":
    print(check_data_server())

