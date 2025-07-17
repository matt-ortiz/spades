from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
from models import init_db, get_db_connection
from auth import send_security_code, verify_security_code, require_login
from scoring import calculate_round_points, calculate_round_points_with_flags, parse_bid, format_bid_display

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database on startup
init_db()

# Template filter for datetime formatting
@app.template_filter('datetime')
def datetime_filter(date_string):
    if date_string:
        try:
            # Handle datetime strings with microseconds
            if '.' in date_string:
                dt = datetime.strptime(date_string.split('.')[0], '%Y-%m-%d %H:%M:%S')
            else:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            return date_string
    return ''

# Template filter for simpler datetime formatting
@app.template_filter('simple_datetime')
def simple_datetime_filter(date_string):
    if date_string:
        try:
            # Handle datetime strings with microseconds
            if '.' in date_string:
                dt = datetime.strptime(date_string.split('.')[0], '%Y-%m-%d %H:%M:%S')
            else:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%m/%d/%Y at %I:%M %p')
        except:
            return date_string
    return ''

# Template filter for bid display formatting
@app.template_filter('format_bid_display')
def format_bid_display_filter(bid_string):
    return format_bid_display(bid_string)

@app.route('/')
@require_login
def dashboard():
    conn = get_db_connection()
    
    # Get user's active games
    active_games = conn.execute('''
        SELECT g.*, 
               CASE WHEN g.team1_final_score >= g.max_score OR g.team2_final_score >= g.max_score 
                    THEN 'completed' ELSE 'active' END as display_status
        FROM games g 
        WHERE g.created_by_user_id = ? AND g.status = 'active'
        ORDER BY g.created_date DESC
    ''', (session['user_id'],)).fetchall()
    
    # Get recent completed games
    completed_games = conn.execute('''
        SELECT * FROM games 
        WHERE created_by_user_id = ? AND status = 'completed'
        ORDER BY completed_date DESC LIMIT 5
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         active_games=active_games, 
                         completed_games=completed_games)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        conn = get_db_connection()
        
        # Check if email already exists
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            flash('Email already registered')
            conn.close()
            return render_template('register.html')
        
        # Create user
        conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if not user:
            flash('Email not found. Please register first.')
            conn.close()
            return render_template('login.html')
        
        # Generate and send security code
        code = secrets.randbelow(900000) + 100000  # 6-digit code
        expires_at = datetime.now() + timedelta(minutes=15)
        
        conn.execute('''
            INSERT INTO auth_codes (user_id, code, expires_at) 
            VALUES (?, ?, ?)
        ''', (user['id'], str(code), expires_at))
        conn.commit()
        conn.close()
        
        # Send email (for now, just flash the code for development)
        if send_security_code(email, code):
            session['pending_user_id'] = user['id']
            flash(f'Security code sent to {email}')
            return redirect(url_for('verify'))
        else:
            flash('Failed to send security code. Please try again.')
    
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'pending_user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        code = request.form['code']
        
        if verify_security_code(session['pending_user_id'], code):
            session['user_id'] = session['pending_user_id']
            del session['pending_user_id']
            
            # Update last login
            conn = get_db_connection()
            conn.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                        (datetime.now(), session['user_id']))
            conn.commit()
            conn.close()
            
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid or expired security code')
    
    return render_template('verify.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/new-game', methods=['GET', 'POST'])
@require_login
def new_game():
    if request.method == 'POST':
        team1_player1 = request.form['team1_player1']
        team1_player2 = request.form['team1_player2']
        team2_player1 = request.form['team2_player1']
        team2_player2 = request.form['team2_player2']
        max_score = int(request.form.get('max_score', 500))
        nil_penalty = int(request.form.get('nil_penalty', 100))
        blind_nil_penalty = int(request.form.get('blind_nil_penalty', 200))
        bag_penalty_threshold = int(request.form.get('bag_penalty_threshold', 10))
        bag_penalty_points = int(request.form.get('bag_penalty_points', 100))
        failed_nil_handling = request.form.get('failed_nil_handling', 'takes_bags')
        
        conn = get_db_connection()
        cursor = conn.execute('''
            INSERT INTO games (
                created_by_user_id, team1_player1, team1_player2, 
                team2_player1, team2_player2, max_score, nil_penalty, 
                blind_nil_penalty, bag_penalty_threshold, bag_penalty_points, 
                failed_nil_handling
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], team1_player1, team1_player2, 
              team2_player1, team2_player2, max_score, nil_penalty, 
              blind_nil_penalty, bag_penalty_threshold, bag_penalty_points, 
              failed_nil_handling))
        
        game_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash('Game created successfully!')
        return redirect(url_for('game', game_id=game_id))
    
    return render_template('new_game.html')

@app.route('/game/<int:game_id>')
@require_login
def game(game_id):
    conn = get_db_connection()
    
    # Get game details
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?', 
                       (game_id, session['user_id'])).fetchone()
    
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Get rounds
    rounds = conn.execute('''
        SELECT * FROM rounds WHERE game_id = ? ORDER BY round_number
    ''', (game_id,)).fetchall()
    
    conn.close()
    
    return render_template('game.html', game=game, rounds=rounds)

@app.route('/game/<int:game_id>/round', methods=['GET', 'POST'])
@require_login
def add_round(game_id):
    conn = get_db_connection()
    
    # Get game details
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?', 
                       (game_id, session['user_id'])).fetchone()
    
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Get current round number
    round_count = conn.execute('SELECT COUNT(*) as count FROM rounds WHERE game_id = ?', 
                              (game_id,)).fetchone()['count']
    round_number = round_count + 1
    
    # Check if there's already a pending round (bids entered but no scores)
    pending_round = conn.execute('''
        SELECT * FROM rounds WHERE game_id = ? AND team1_actual IS NULL 
        ORDER BY round_number DESC LIMIT 1
    ''', (game_id,)).fetchone()
    
    if request.method == 'POST':
        team1_bid = request.form['team1_bid']
        team2_bid = request.form['team2_bid']
        
        if pending_round:
            # Update existing round with bids
            conn.execute('''
                UPDATE rounds SET team1_bid = ?, team2_bid = ? WHERE id = ?
            ''', (team1_bid, team2_bid, pending_round['id']))
        else:
            # Create new round with just bids
            conn.execute('''
                INSERT INTO rounds (game_id, round_number, team1_bid, team2_bid) 
                VALUES (?, ?, ?, ?)
            ''', (game_id, round_number, team1_bid, team2_bid))
        
        conn.commit()
        conn.close()
        
        flash('Bids saved! Now enter the actual scores.')
        return redirect(url_for('enter_scores', game_id=game_id))
    
    conn.close()
    return render_template('bid_form.html', game=game, round_number=round_number)

@app.route('/game/<int:game_id>/scores', methods=['GET', 'POST'])
@require_login
def enter_scores(game_id):
    conn = get_db_connection()
    
    # Get game details
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?', 
                       (game_id, session['user_id'])).fetchone()
    
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Get the pending round (with bids but no scores)
    pending_round = conn.execute('''
        SELECT * FROM rounds WHERE game_id = ? AND team1_actual IS NULL 
        ORDER BY round_number DESC LIMIT 1
    ''', (game_id,)).fetchone()
    
    if not pending_round:
        flash('No pending round found. Please enter bids first.')
        conn.close()
        return redirect(url_for('add_round', game_id=game_id))
    
    if request.method == 'POST':
        team1_actual = int(request.form['team1_actual'])
        team2_actual = int(request.form['team2_actual'])
        
        # Validate totals equal 13
        if team1_actual + team2_actual != 13:
            flash('Team totals must equal 13')
            conn.close()
            return render_template('score_form.html', game=game, round=pending_round)
        
        # Get special bid success flags
        team1_nil_success = request.form.get('team1_nil_success') == 'on'
        team1_blind_nil_success = request.form.get('team1_blind_nil_success') == 'on'
        team1_blind_success = request.form.get('team1_blind_success') == 'on'
        
        team2_nil_success = request.form.get('team2_nil_success') == 'on'
        team2_blind_nil_success = request.form.get('team2_blind_nil_success') == 'on'
        team2_blind_success = request.form.get('team2_blind_success') == 'on'
        
        # Calculate points using the new function with success flags
        team1_points = calculate_round_points_with_flags(
            pending_round['team1_bid'], team1_actual, game,
            team1_nil_success, team1_blind_nil_success, team1_blind_success
        )
        team2_points = calculate_round_points_with_flags(
            pending_round['team2_bid'], team2_actual, game,
            team2_nil_success, team2_blind_nil_success, team2_blind_success
        )
        
        # Get current totals
        last_completed_round = conn.execute('''
            SELECT team1_total, team2_total, team1_bags_total, team2_bags_total 
            FROM rounds WHERE game_id = ? AND team1_actual IS NOT NULL 
            ORDER BY round_number DESC LIMIT 1
        ''', (game_id,)).fetchone()
        
        if last_completed_round:
            team1_total = last_completed_round['team1_total'] + team1_points
            team2_total = last_completed_round['team2_total'] + team2_points
            team1_bags_total = last_completed_round['team1_bags_total']
            team2_bags_total = last_completed_round['team2_bags_total']
        else:
            team1_total = team1_points
            team2_total = team2_points
            team1_bags_total = 0
            team2_bags_total = 0
        
        # Calculate bags earned this round
        team1_bags_earned = max(0, team1_actual - int(parse_bid(pending_round['team1_bid'])[0]))
        team2_bags_earned = max(0, team2_actual - int(parse_bid(pending_round['team2_bid'])[0]))
        
        # Update bag totals
        team1_bags_total += team1_bags_earned
        team2_bags_total += team2_bags_earned
        
        # Check for bag penalties
        if team1_bags_total >= game['bag_penalty_threshold']:
            team1_total -= game['bag_penalty_points']
            team1_bags_total = 0
        
        if team2_bags_total >= game['bag_penalty_threshold']:
            team2_total -= game['bag_penalty_points']
            team2_bags_total = 0
        
        # Update round with scores
        conn.execute('''
            UPDATE rounds SET 
                team1_actual = ?, team2_actual = ?, team1_points = ?, team2_points = ?,
                team1_total = ?, team2_total = ?, team1_bags_earned = ?, team2_bags_earned = ?,
                team1_bags_total = ?, team2_bags_total = ?
            WHERE id = ?
        ''', (team1_actual, team2_actual, team1_points, team2_points,
              team1_total, team2_total, team1_bags_earned, team2_bags_earned,
              team1_bags_total, team2_bags_total, pending_round['id']))
        
        # Update game totals
        conn.execute('''
            UPDATE games SET 
                team1_final_score = ?, team2_final_score = ?,
                team1_bags = ?, team2_bags = ?
            WHERE id = ?
        ''', (team1_total, team2_total, team1_bags_total, team2_bags_total, game_id))
        
        # Check for game completion
        if team1_total >= game['max_score'] or team2_total >= game['max_score']:
            if team1_total >= game['max_score']:
                winner = f"{game['team1_player1']} & {game['team1_player2']}"
            else:
                winner = f"{game['team2_player1']} & {game['team2_player2']}"
            conn.execute('''
                UPDATE games SET status = 'completed', winner = ?, completed_date = ?
                WHERE id = ?
            ''', (winner, datetime.now(), game_id))
        
        conn.commit()
        conn.close()
        
        flash('Round completed successfully!')
        return redirect(url_for('game', game_id=game_id))
    
    conn.close()
    return render_template('score_form.html', game=game, round=pending_round)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)