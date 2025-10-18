"""
Database Migration Runner
-------------------------
Run this script to apply database migrations for chat persistence.

Usage:
    python -m db.run_migration

This will:
1. Test database connection
2. Create chat_sessions and messages tables
3. Create necessary indexes and triggers
"""

import os
import sys
from pathlib import Path
from .connection import get_db

def test_connection():
    """Test database connection before running migrations."""
    print("🔍 Testing database connection...")
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL: {version[:50]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_migration(migration_file: str):
    """Run a single migration file."""
    print(f"\n📄 Running migration: {migration_file}")
    
    try:
        # Read migration SQL
        migration_path = Path(__file__).parent / "migrations" / migration_file
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Execute migration
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        
        print(f"✅ Migration completed: {migration_file}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_documents_v2_table():
    """Verify that documents_v2 table was created successfully."""
    print("\n🔍 Verifying documents_v2 table...")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check documents_v2 table
        cursor.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents_v2'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("\n✅ Table 'documents_v2' created with columns:")
            for table, column, dtype in columns:
                print(f"   - {column}: {dtype}")
        else:
            print("❌ Table 'documents_v2' not found")
            return False
        
        # Check indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'documents_v2'
            ORDER BY indexname;
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            print("\n✅ Indexes created:")
            for (idx_name,) in indexes:
                print(f"   - {idx_name}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def verify_international_policy_table():
    """Verify that international_policy table was created successfully."""
    print("\n🔍 Verifying international_policy table...")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check international_policy table
        cursor.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'international_policy'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("\n✅ Table 'international_policy' created with columns:")
            for table, column, dtype in columns:
                print(f"   - {column}: {dtype}")
        else:
            print("❌ Table 'international_policy' not found")
            return False
        
        # Check indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'international_policy'
            ORDER BY indexname;
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            print("\n✅ Indexes created:")
            for (idx_name,) in indexes:
                print(f"   - {idx_name}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main migration runner."""
    print("=" * 60)
    print("🚀 Database Migration Runner")
    print("=" * 60)
    
    # Step 1: Test connection
    if not test_connection():
        print("\n❌ Migration aborted: Cannot connect to database")
        print("\nPlease check your .env file contains:")
        print("  - DB_NAME")
        print("  - DB_USER")
        print("  - DB_PASSWORD")
        print("  - DB_HOST")
        print("  - DB_PORT")
        sys.exit(1)
    
    # Step 2: Run documents_v2 migration
    if not run_migration("003_create_documents_v2_table.sql"):
        print("\n❌ Migration failed")
        sys.exit(1)
    
    # Step 3: Run international_policy migration
    if not run_migration("004_create_international_policy_table.sql"):
        print("\n❌ Migration failed")
        sys.exit(1)
    
    # Step 4: Verify tables
    if not verify_documents_v2_table():
        print("\n❌ Documents V2 verification failed")
        sys.exit(1)
    
    if not verify_international_policy_table():
        print("\n❌ International Policy verification failed")
        sys.exit(1)
    
    if not verify_international_policy_table():
        print("\n❌ Verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 All Migrations completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review the created tables in your database")
    print("  2. Test the new /upload_v2 endpoint for company documents")
    print("  3. Test international policy document uploads")
    print("  4. Use RetrieverV2 for citation-enabled company document retrieval")
    print("  5. Use InternationalPolicyRetriever for international regulation retrieval")
    print()

if __name__ == "__main__":
    main()
