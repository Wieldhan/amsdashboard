import sqlite3
import hashlib

def update_admin_access():
    try:
        conn = sqlite3.connect('./database/user_auth.db')
        cursor = conn.cursor()
        
        # Update admin's tab access and password hash
        password_hash = hashlib.sha256("1122".encode()).hexdigest()
        cursor.execute("""
            UPDATE users 
            SET tab_access = 'all',
                password_hash = ?
            WHERE user_id = 'admin'
        """, (password_hash,))
        
        conn.commit()
        print("Admin access and password updated successfully")
        
    except Exception as e:
        print(f"Error updating admin access: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    update_admin_access()