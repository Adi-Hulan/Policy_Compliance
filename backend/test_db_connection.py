"""
Quick database connection test
Run this before applying migrations
"""

from db.connection import get_db

def test_db_connection():
    try:
        print("Testing database connection...")
        conn = get_db()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT current_database(), current_user, version();")
        db_name, user, version = cursor.fetchone()
        
        print(f"✅ Connected successfully!")
        print(f"   Database: {db_name}")
        print(f"   User: {user}")
        print(f"   Version: {version[:60]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check your .env file and database credentials.")
        return False

if __name__ == "__main__":
    test_db_connection()
