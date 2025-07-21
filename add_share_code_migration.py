#!/usr/bin/env python3
"""
Migration script to add share_code column to games table
"""
import sqlite3
import uuid
from models import get_db_connection

def add_share_code_column():
    """Add share_code column to games table and generate codes for existing games"""
    conn = get_db_connection()
    
    try:
        # Check if column already exists
        cursor = conn.execute("PRAGMA table_info(games)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'share_code' not in columns:
            print("Adding share_code column to games table...")
            conn.execute('ALTER TABLE games ADD COLUMN share_code TEXT')
            
            # Generate share codes for existing games
            print("Generating share codes for existing games...")
            games = conn.execute('SELECT id FROM games').fetchall()
            
            for game in games:
                share_code = str(uuid.uuid4()).replace('-', '')[:12]  # 12-char code
                conn.execute('UPDATE games SET share_code = ? WHERE id = ?', (share_code, game['id']))
            
            conn.commit()
            print("Successfully added share codes to {} existing games".format(len(games)))
        else:
            print("share_code column already exists")
            
    except Exception as e:
        print("Error during migration: {}".format(e))
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    add_share_code_column()