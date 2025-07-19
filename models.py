import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DATABASE = 'database.db'

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=1000')
    conn.execute('PRAGMA temp_store=memory')
    return conn

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT DEFAULT '',
            email TEXT UNIQUE NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Auth codes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS auth_codes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Games table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            created_by_user_id INTEGER NOT NULL,
            team1_player1 TEXT NOT NULL,
            team1_player2 TEXT NOT NULL,
            team2_player1 TEXT NOT NULL,
            team2_player2 TEXT NOT NULL,
            max_score INTEGER DEFAULT 500,
            nil_penalty INTEGER DEFAULT 100,
            blind_nil_penalty INTEGER DEFAULT 200,
            bag_penalty_threshold INTEGER DEFAULT 10,
            bag_penalty_points INTEGER DEFAULT 100,
            failed_nil_handling TEXT DEFAULT 'takes_bags',
            status TEXT DEFAULT 'active',
            team1_final_score INTEGER DEFAULT 0,
            team2_final_score INTEGER DEFAULT 0,
            team1_bags INTEGER DEFAULT 0,
            team2_bags INTEGER DEFAULT 0,
            winner TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_date TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users (id)
        )
    ''')
    
    # Rounds table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY,
            game_id INTEGER NOT NULL,
            round_number INTEGER NOT NULL,
            team1_bid TEXT,
            team2_bid TEXT,
            team1_actual INTEGER,
            team2_actual INTEGER,
            team1_points INTEGER,
            team2_points INTEGER,
            team1_total INTEGER,
            team2_total INTEGER,
            team1_bags_earned INTEGER DEFAULT 0,
            team2_bags_earned INTEGER DEFAULT 0,
            team1_bags_total INTEGER DEFAULT 0,
            team2_bags_total INTEGER DEFAULT 0,
            
            -- Success/failure flags for special bids
            team1_nil_success BOOLEAN DEFAULT NULL,
            team1_blind_nil_success BOOLEAN DEFAULT NULL, 
            team1_blind_success BOOLEAN DEFAULT NULL,
            team2_nil_success BOOLEAN DEFAULT NULL,
            team2_blind_nil_success BOOLEAN DEFAULT NULL,
            team2_blind_success BOOLEAN DEFAULT NULL,
            
            -- Scoring components breakdown (clear paper trail)
            team1_bid_points INTEGER DEFAULT 0,
            team1_nil_bonus INTEGER DEFAULT 0,
            team1_blind_nil_bonus INTEGER DEFAULT 0,
            team1_blind_bonus INTEGER DEFAULT 0,
            team1_bag_points INTEGER DEFAULT 0,
            team1_bag_penalty INTEGER DEFAULT 0,
            
            team2_bid_points INTEGER DEFAULT 0,
            team2_nil_bonus INTEGER DEFAULT 0,
            team2_blind_nil_bonus INTEGER DEFAULT 0,
            team2_blind_bonus INTEGER DEFAULT 0,
            team2_bag_points INTEGER DEFAULT 0,
            team2_bag_penalty INTEGER DEFAULT 0,
            
            -- Bag tracking for penalties
            team1_bags_before_penalty INTEGER DEFAULT 0,
            team2_bags_before_penalty INTEGER DEFAULT 0,
            
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")