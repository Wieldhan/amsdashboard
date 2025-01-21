import sqlite3
import hashlib
import os
from typing import List, Optional, Dict
import streamlit as st

class UserManagement:
    def __init__(self):
        # Ensure data directory exists
        os.makedirs("./database", exist_ok=True)
        self.db_path = "./database/user_auth.db"
        self._init_database()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id TEXT PRIMARY KEY,
                     password_hash TEXT NOT NULL,
                     is_admin BOOLEAN NOT NULL,
                     branch_access TEXT NOT NULL,
                     tab_access TEXT NOT NULL)''')
        
        # Create default admin if not exists
        c.execute("SELECT * FROM users WHERE user_id = 'admin'")
        if not c.fetchone():
            # Default password: admin123
            default_password = hashlib.sha256("admin1122".encode()).hexdigest()
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                     ("admin", default_password, True, "all", "all"))
        
        conn.commit()
        conn.close()
    
    def verify_password(self, user_id: str, password: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        conn.close()
        return result and result[0] == password_hash
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        if not self.verify_password(user_id, old_password):
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        c.execute("UPDATE users SET password_hash = ? WHERE user_id = ?",
                 (new_password_hash, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    def create_user(self, user_id: str, password: str, branch_access: str, tab_access: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                     (user_id, password_hash, False, branch_access, tab_access))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_user_access(self, user_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT is_admin, branch_access, tab_access FROM users WHERE user_id = ?",
                 (user_id,))
        result = c.fetchone()
        
        conn.close()
        
        if result:
            return {
                "is_admin": bool(result[0]),
                "branch_access": result[1],
                "tab_access": result[2]
            }
        return None
    
    def get_all_users(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT user_id, is_admin, branch_access, tab_access FROM users")
        users = c.fetchall()
        
        conn.close()
        
        return [{
            "user_id": user[0],
            "is_admin": bool(user[1]),
            "branch_access": user[2],
            "tab_access": user[3]
        } for user in users]
    
    def update_user_access(self, user_id: str, branch_access: str, tab_access: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("UPDATE users SET branch_access = ?, tab_access = ? WHERE user_id = ?",
                     (branch_access, tab_access, user_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def delete_user(self, user_id: str) -> bool:
        if user_id == "admin":  # Prevent admin deletion
            return False
            
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def admin_change_password(self, user_id: str, new_password: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            c.execute("UPDATE users SET password_hash = ? WHERE user_id = ?",
                     (new_password_hash, user_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close() 