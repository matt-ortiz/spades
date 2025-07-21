#!/usr/bin/env python3
"""
Migration script to update existing games with 5-digit share codes
"""
import secrets
from models import get_db_connection

def update_to_5_digit_codes():
    """Update all games to use 5-digit share codes"""
    conn = get_db_connection()
    
    try:
        # Get all games that need new share codes
        games = conn.execute('SELECT id, share_code FROM games').fetchall()
        
        print("Updating {} games to 5-digit share codes...".format(len(games)))
        
        for game in games:
            # Generate new 5-digit code
            new_code = str(secrets.randbelow(90000) + 10000)  # 10000-99999
            
            # Check for collision (unlikely but good practice)
            while conn.execute('SELECT id FROM games WHERE share_code = ?', (new_code,)).fetchone():
                new_code = str(secrets.randbelow(90000) + 10000)
            
            # Update the game
            conn.execute('UPDATE games SET share_code = ? WHERE id = ?', (new_code, game['id']))
            print("Game {}: {} -> {}".format(game['id'], game['share_code'], new_code))
        
        conn.commit()
        print("Successfully updated all games to 5-digit codes!")
        
    except Exception as e:
        print("Error during migration: {}".format(e))
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    update_to_5_digit_codes()