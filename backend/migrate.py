import sqlite3
from pathlib import Path
import urllib.parse
from .db import DATABASE_URL, engine

def migrate_db():
    print("🔄 Running database migrations...")
    
    # Check if DATABASE_URL is SQLite or Postgres
    if DATABASE_URL.startswith("sqlite"):
        # Extract path
        # Format is sqlite:///path/to/events.db or sqlite:///events.db
        path_str = DATABASE_URL.replace("sqlite:///", "")
        db_path = Path(path_str)
        
        print(f"   Connecting to SQLite database at {db_path.absolute()}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Check if table users exists and check constraints on hashed_password
        try:
            cursor.execute("PRAGMA table_info(users);")
            columns = cursor.fetchall()
            
            if columns:
                # columns format is: (cid, name, type, notnull, dflt_value, pk)
                hashed_password_notnull = False
                for col in columns:
                    if col[1] == "hashed_password" and col[3] == 1:
                        hashed_password_notnull = True
                        break
                
                if hashed_password_notnull:
                    print("   ⚠️ Column users.hashed_password is set to NOT NULL in SQLite. Rebuilding table to allow null...")
                    # Begin a transaction
                    cursor.execute("BEGIN TRANSACTION;")
                    try:
                        # Rename table
                        cursor.execute("ALTER TABLE users RENAME TO users_old;")
                        
                        # Create new table with nullable hashed_password and all fields
                        cursor.execute("""
                        CREATE TABLE users (
                            id VARCHAR NOT NULL PRIMARY KEY,
                            email VARCHAR NOT NULL UNIQUE,
                            hashed_password VARCHAR,
                            google_id VARCHAR UNIQUE,
                            discord_id VARCHAR UNIQUE,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        );
                        """)
                        
                        # Determine which columns exist in old table
                        cursor.execute("PRAGMA table_info(users_old);")
                        old_cols = [c[1] for c in cursor.fetchall()]
                        
                        copy_cols = [c for c in ["id", "email", "hashed_password", "google_id", "discord_id", "created_at"] if c in old_cols]
                        cols_str = ", ".join(copy_cols)
                        
                        cursor.execute(f"INSERT INTO users ({cols_str}) SELECT {cols_str} FROM users_old;")
                        cursor.execute("DROP TABLE users_old;")
                        
                        conn.commit()
                        print("   ✅ Rebuilt users table successfully.")
                    except Exception as re:
                        conn.rollback()
                        print(f"   ❌ Failed to rebuild users table: {re}")
            else:
                print("   ℹ️ Table users does not exist yet. It will be created with correct constraints.")
        except Exception as e:
            print(f"   ⚠️ Error checking users table structure: {e}")
            
        # 2. Add google_id and discord_id columns to users if they don't exist
        # (This is a fallback/safety check in case they are not in the existing table and it was not rebuilt)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR;")
            print("   ✅ Added google_id column to users table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("   ℹ️ Column google_id already exists in users table")
            else:
                print(f"   ⚠️ Error adding google_id: {e}")
                
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN discord_id VARCHAR;")
            print("   ✅ Added discord_id column to users table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("   ℹ️ Column discord_id already exists in users table")
            else:
                print(f"   ⚠️ Error adding discord_id: {e}")

        # 3. Drop link_codes table if it exists
        try:
            cursor.execute("DROP TABLE IF EXISTS link_codes;")
            print("   ✅ Dropped obsolete link_codes table")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️ Error dropping link_codes table: {e}")
            
        conn.commit()
        conn.close()
        print("   ✅ SQLite migration complete.")
        
    elif DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres"):
        # For Postgres (Railway free/paid DB)
        print("   Connecting to Postgres database...")
        from sqlalchemy import text
        
        # Let's run individual connections to avoid transaction abort blocks
        # 1. Try google_id
        try:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR;"))
            print("   ✅ Added google_id column to users table")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️ Column google_id already exists in users table")
            else:
                print(f"   ⚠️ Error adding google_id: {e}")

        # 2. Try discord_id
        try:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN discord_id VARCHAR;"))
            print("   ✅ Added discord_id column to users table")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️ Column discord_id already exists in users table")
            else:
                print(f"   ⚠️ Error adding discord_id: {e}")

        # 3. Remove NOT NULL from users.hashed_password
        try:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;"))
            print("   ✅ Removed NOT NULL constraint from users.hashed_password")
        except Exception as e:
            print(f"   ⚠️ Error removing NOT NULL from hashed_password: {e}")

        # 4. Drop link_codes
        try:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS link_codes;"))
            print("   ✅ Dropped obsolete link_codes table")
        except Exception as e:
            print(f"   ⚠️ Error dropping link_codes table: {e}")
            
        print("   ✅ Postgres migration complete.")
    else:
        print(f"   ⚠️ Unknown database type for URL: {DATABASE_URL}")

if __name__ == "__main__":
    migrate_db()
