from sqlalchemy import text
from src.backend.database_funding import get_engine

def get_branch_mapping():

    try:
        engine = get_engine()
        
        # Get branch mapping, excluding code '99'
        branch_query = text("""
            SELECT KodeCabang, NamaCabang 
            FROM AMS.dbo.PICabang
            WHERE KodeCabang != '99'
        """)
        
        with engine.connect() as conn:
            branches = {row[0]: row[1] for row in conn.execute(branch_query)}
            
        return branches
        
    except Exception as e:
        print(f"Error fetching branch mappings: {str(e)}")
        return {} 
    
if __name__ == "__main__":
    print(get_branch_mapping())

