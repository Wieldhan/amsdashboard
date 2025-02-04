from sqlalchemy import text
from backend.database_funding import get_engine

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

