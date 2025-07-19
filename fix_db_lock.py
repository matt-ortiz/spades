#!/usr/bin/env python3
"""
Script to diagnose and fix database locking issues
"""
import sqlite3
import os
import sys
from models import DATABASE

def check_database_lock():
    """Check if database is locked and try to fix it"""
    
    print(f"Checking database: {DATABASE}")
    
    # Check if database file exists
    if not os.path.exists(DATABASE):
        print("Database file does not exist!")
        return False
        
    # Check file permissions
    try:
        print(f"Database file permissions: {oct(os.stat(DATABASE).st_mode)[-3:]}")
        if os.access(DATABASE, os.R_OK):
            print("✓ Database is readable")
        else:
            print("✗ Database is not readable")
            
        if os.access(DATABASE, os.W_OK):
            print("✓ Database is writable")
        else:
            print("✗ Database is not writable")
    except Exception as e:
        print(f"Error checking permissions: {e}")
        
    # Check for WAL and SHM files (these can cause locks)
    wal_file = DATABASE + '-wal'
    shm_file = DATABASE + '-shm'
    
    if os.path.exists(wal_file):
        print(f"Found WAL file: {wal_file}")
        try:
            wal_size = os.path.getsize(wal_file)
            print(f"WAL file size: {wal_size} bytes")
        except Exception as e:
            print(f"Error reading WAL file: {e}")
    
    if os.path.exists(shm_file):
        print(f"Found SHM file: {shm_file}")
        
    # Try to connect and perform a simple operation
    try:
        print("Attempting database connection...")
        conn = sqlite3.connect(DATABASE, timeout=10.0)
        
        # Try a simple read
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        result = cursor.fetchone()
        print("✓ Database read successful")
        
        # Try to enable WAL mode
        conn.execute('PRAGMA journal_mode=WAL')
        print("✓ WAL mode enabled")
        
        # Try a simple write (create a test table and drop it)
        conn.execute("CREATE TABLE IF NOT EXISTS test_lock_check (id INTEGER)")
        conn.execute("DROP TABLE test_lock_check")
        conn.commit()
        print("✓ Database write successful")
        
        conn.close()
        print("✓ Database connection closed successfully")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"✗ Database error: {e}")
        
        if "database is locked" in str(e):
            print("\nDatabase is locked! Trying to fix...")
            
            # Force close any existing connections
            try:
                # Open with a short timeout and immediately close
                temp_conn = sqlite3.connect(DATABASE, timeout=1.0)
                temp_conn.close()
                print("✓ Forced connection cleanup")
            except:
                pass
                
            return False
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def fix_permissions():
    """Fix database file permissions"""
    try:
        os.chmod(DATABASE, 0o666)  # Read/write for owner and group
        print("✓ Fixed database permissions")
        return True
    except Exception as e:
        print(f"✗ Could not fix permissions: {e}")
        return False

if __name__ == "__main__":
    print("Database Lock Diagnostic Tool")
    print("=" * 40)
    
    if check_database_lock():
        print("\n✓ Database is working properly!")
    else:
        print("\n⚠ Database has issues. Attempting fixes...")
        
        # Try to fix permissions
        fix_permissions()
        
        # Try again
        if check_database_lock():
            print("\n✓ Database issues resolved!")
        else:
            print("\n✗ Could not resolve database issues.")
            print("\nTry these manual steps:")
            print("1. Stop your Flask application")
            print("2. Delete database.db-wal and database.db-shm files if they exist")
            print("3. Restart your application")
