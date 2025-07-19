#!/usr/bin/env python3
"""
Reset database script - removes existing database and recreates with new schema
"""
import os
from models import init_db, DATABASE

def reset_database():
    """Remove existing database and create new one with updated schema"""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Removed existing database: {DATABASE}")
    
    # Initialize with new schema
    init_db()
    print("Database reset and initialized with new schema!")
    print("\nNew rounds table includes:")
    print("- Special bid success/failure flags")
    print("- Detailed scoring component breakdown")
    print("- Bag penalty tracking")

if __name__ == '__main__':
    reset_database()