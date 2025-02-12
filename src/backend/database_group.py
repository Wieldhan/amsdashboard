from sqlalchemy import text
from src.backend.database_funding import get_engine

def get_grup1_mapping():

    try:
        engine = get_engine()
        
        branch_query = text("""
            SELECT
            KodeGrup1, 
            "Nama Grup",
            Keterangan
            FROM AMSPinjaman.dbo.LnTbGrup1
        """)

        with engine.connect() as conn:
            branches = {row[0]: row[1] for row in conn.execute(branch_query)}
            
        return branches
        
    except Exception as e:
        print(f"Error fetching group 1 mappings: {str(e)}")
        return {}
    
def get_grup2_mapping():

    try:
        engine = get_engine()
        
        branch_query = text("""
            SELECT
            KodeGrup2, 
            "Nama Grup",
            Keterangan
            FROM AMSPinjaman.dbo.LnTbGrup2
        """)
        
        with engine.connect() as conn:
            branches = {row[0]: row[1] for row in conn.execute(branch_query)}
            
        return branches
        
    except Exception as e:
        print(f"Error fetching group 2 mappings: {str(e)}")
        return {} 
    

if __name__ == "__main__":
    print(get_grup1_mapping())
    print(get_grup2_mapping())
