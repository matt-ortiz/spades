from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import secrets
import uuid
from models import init_db, get_db_connection
from auth import send_security_code, verify_security_code, require_login, cleanup_expired_codes
from scoring import calculate_round_points, calculate_round_points_with_flags, parse_bid, format_bid_display, format_made_display, get_score_breakdown_detailed, calculate_detailed_round_scoring

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Make sessions permanent (never expire unless user logs out)
app.permanent_session_lifetime = timedelta(days=365)  # 1 year

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

# Template filter for score+bags display (score in 10s, bags in ones digit)
@app.template_filter('score_with_bags')
def score_with_bags_filter(score, bags):
    """Combine score (multiples of 10) with bags (ones digit) for display.
    Bags appear in the ones digit. For negative scores, bags make it more negative.
    Example: score=-40, bags=2 → display as -42 (-40 - 2)
    Example: score=60, bags=5 → display as 65 (60 + 5)
    """
    if score is None:
        score = 0
    if bags is None:
        bags = 0

    # For negative scores, subtract bags (makes it more negative)
    # For positive scores, add bags
    if score < 0:
        return score - bags
    else:
        return score + bags

# Template global function for score breakdown
@app.template_global()
def get_score_breakdown_detailed_template(round_data):
    return get_score_breakdown_detailed(round_data)

@app.route('/')
def homepage():
    # Check if user is logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    return render_template('homepage.html')

@app.route('/dashboard')
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

    # Get abandoned games
    abandoned_games = conn.execute('''
        SELECT * FROM games
        WHERE created_by_user_id = ? AND status = 'abandoned'
        ORDER BY created_date DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         active_games=active_games, 
                         completed_games=completed_games,
                         abandoned_games=abandoned_games)

# Registration route removed - users are created automatically on first login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            
            if not user:
                # Create user automatically with email as name (can be ignored later)
                name = email.split('@')[0]  # Use part before @ as default name
                cursor = conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
                user_id = cursor.lastrowid
                conn.commit()  # Commit the user creation immediately
                user = {'id': user_id, 'name': name, 'email': email}
            
            # Clean up old codes periodically
            cleanup_expired_codes()
            
            # Generate and send security code
            code = secrets.randbelow(900000) + 100000  # 6-digit code
            expires_at = datetime.now() + timedelta(minutes=15)
            
            conn.execute('''
                INSERT INTO auth_codes (user_id, code, expires_at) 
                VALUES (?, ?, ?)
            ''', (user['id'], str(code), expires_at))
            conn.commit()
            
            # Send email (for now, just flash the code for development)
            if send_security_code(email, code):
                session['pending_user_id'] = user['id']
                flash('Security code sent to {}'.format(email))
                return redirect(url_for('verify'))
            else:
                flash('Failed to send security code. Please try again.')
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                flash('Database is temporarily busy. Please try again in a moment.')
            else:
                flash('Database error occurred. Please try again.')
            print("Database error in login: {}".format(e))
        except Exception as e:
            flash('An error occurred. Please try again.')
            print("Unexpected error in login: {}".format(e))
        finally:
            try:
                conn.close()
            except:
                pass
    
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'pending_user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        code = request.form['code']
        
        if verify_security_code(session['pending_user_id'], code):
            session['user_id'] = session['pending_user_id']
            session.permanent = True  # Make session persistent
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
        
        # Generate 5-digit share code
        share_code = str(secrets.randbelow(90000) + 10000)  # 10000-99999
        
        conn = get_db_connection()
        cursor = conn.execute('''
            INSERT INTO games (
                created_by_user_id, team1_player1, team1_player2, 
                team2_player1, team2_player2, max_score, nil_penalty, 
                blind_nil_penalty, bag_penalty_threshold, bag_penalty_points, share_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], team1_player1, team1_player2, 
              team2_player1, team2_player2, max_score, nil_penalty, 
              blind_nil_penalty, bag_penalty_threshold, bag_penalty_points, share_code))
        
        game_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash('Game created successfully!')
        return redirect(url_for('game', game_id=game_id))
    
    return render_template('new_game.html')

@app.route('/view/<share_code>')
def view_game(share_code):
    """Public spectator view - no authentication required"""
    conn = get_db_connection()
    
    # Get game by share code
    game = conn.execute('SELECT * FROM games WHERE share_code = ?', (share_code,)).fetchone()
    
    if not game:
        flash('Game not found or invalid share code')
        conn.close()
        return render_template('homepage.html')
    
    # Get rounds
    rounds = conn.execute('''
        SELECT * FROM rounds WHERE game_id = ? ORDER BY round_number
    ''', (game['id'],)).fetchall()
    
    conn.close()
    
    # Render spectator template (read-only version of game.html)
    return render_template('spectator.html', game=game, rounds=rounds)

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
        
        # Calculate detailed scoring components for both teams
        team1_scoring = calculate_detailed_round_scoring(
            pending_round['team1_bid'], team1_actual, game,
            team1_nil_success, team1_blind_nil_success, team1_blind_success
        )
        team2_scoring = calculate_detailed_round_scoring(
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
            team1_bags_total = last_completed_round['team1_bags_total']
            team2_bags_total = last_completed_round['team2_bags_total']
        else:
            team1_bags_total = 0
            team2_bags_total = 0
        
        # Calculate bags earned this round
        team1_bags_earned = max(0, team1_actual - int(parse_bid(pending_round['team1_bid'])[0]))
        team2_bags_earned = max(0, team2_actual - int(parse_bid(pending_round['team2_bid'])[0]))
        
        # Store bags before penalty for tracking
        team1_bags_before_penalty = team1_bags_total + team1_bags_earned
        team2_bags_before_penalty = team2_bags_total + team2_bags_earned
        
        # Update bag totals
        team1_bags_total += team1_bags_earned
        team2_bags_total += team2_bags_earned
        
        # Check for bag penalties and apply them (multiple penalties if needed)
        team1_bag_penalty = 0
        team2_bag_penalty = 0

        # Apply penalty for each complete set of bags (e.g., 23 bags = 2 penalties, 3 remaining)
        while team1_bags_total >= game['bag_penalty_threshold']:
            team1_bag_penalty += game['bag_penalty_points']
            team1_bags_total -= game['bag_penalty_threshold']

        while team2_bags_total >= game['bag_penalty_threshold']:
            team2_bag_penalty += game['bag_penalty_points']
            team2_bags_total -= game['bag_penalty_threshold']
        
        # Calculate final round points including bag penalties
        team1_points = team1_scoring['total_points'] - team1_bag_penalty
        team2_points = team2_scoring['total_points'] - team2_bag_penalty
        
        # Calculate new totals
        if last_completed_round:
            team1_total = last_completed_round['team1_total'] + team1_points
            team2_total = last_completed_round['team2_total'] + team2_points
        else:
            team1_total = team1_points
            team2_total = team2_points
        
        # Update round with all detailed scoring data
        conn.execute('''
            UPDATE rounds SET 
                team1_actual = ?, team2_actual = ?, team1_points = ?, team2_points = ?,
                team1_total = ?, team2_total = ?, team1_bags_earned = ?, team2_bags_earned = ?,
                team1_bags_total = ?, team2_bags_total = ?,
                team1_nil_success = ?, team1_blind_nil_success = ?, team1_blind_success = ?,
                team2_nil_success = ?, team2_blind_nil_success = ?, team2_blind_success = ?,
                team1_bid_points = ?, team1_nil_bonus = ?, team1_blind_nil_bonus = ?, 
                team1_blind_bonus = ?, team1_bag_points = ?, team1_bag_penalty = ?,
                team2_bid_points = ?, team2_nil_bonus = ?, team2_blind_nil_bonus = ?, 
                team2_blind_bonus = ?, team2_bag_points = ?, team2_bag_penalty = ?,
                team1_bags_before_penalty = ?, team2_bags_before_penalty = ?
            WHERE id = ?
        ''', (team1_actual, team2_actual, team1_points, team2_points,
              team1_total, team2_total, team1_bags_earned, team2_bags_earned,
              team1_bags_total, team2_bags_total,
              team1_nil_success, team1_blind_nil_success, team1_blind_success,
              team2_nil_success, team2_blind_nil_success, team2_blind_success,
              team1_scoring['bid_points'], team1_scoring['nil_bonus'], team1_scoring['blind_nil_bonus'],
              team1_scoring['blind_bonus'], team1_scoring['bag_points'], team1_bag_penalty,
              team2_scoring['bid_points'], team2_scoring['nil_bonus'], team2_scoring['blind_nil_bonus'],
              team2_scoring['blind_bonus'], team2_scoring['bag_points'], team2_bag_penalty,
              team1_bags_before_penalty, team2_bags_before_penalty, pending_round['id']))
        
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
                winner = "{} & {}".format(game['team1_player1'], game['team1_player2'])
            else:
                winner = "{} & {}".format(game['team2_player1'], game['team2_player2'])
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

@app.route('/game/<int:game_id>/round/<int:round_id>/edit-bids', methods=['GET', 'POST'])
@require_login
def edit_bids(game_id, round_id):
    conn = get_db_connection()
    
    # Get game details
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?', 
                       (game_id, session['user_id'])).fetchone()
    
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Get the specific round
    round_data = conn.execute('SELECT * FROM rounds WHERE id = ? AND game_id = ?', 
                             (round_id, game_id)).fetchone()
    
    if not round_data:
        flash('Round not found')
        conn.close()
        return redirect(url_for('game', game_id=game_id))
    
    # Check if scores have already been entered (prevent editing if scores exist)
    if round_data['team1_actual'] is not None:
        flash('Cannot edit bids after scores have been entered')
        conn.close()
        return redirect(url_for('game', game_id=game_id))
    
    if request.method == 'POST':
        team1_bid = request.form['team1_bid']
        team2_bid = request.form['team2_bid']
        
        # Update the round with new bids
        conn.execute('''
            UPDATE rounds SET team1_bid = ?, team2_bid = ? WHERE id = ?
        ''', (team1_bid, team2_bid, round_id))
        
        conn.commit()
        conn.close()
        
        flash('Bids updated successfully!')
        return redirect(url_for('enter_scores', game_id=game_id))
    
    conn.close()
    return render_template('edit_bids.html', game=game, round=round_data)

def recalculate_from_round(conn, game_id, start_round_number):
    """Recalculate all round totals from a given round number onwards.
    Call this after editing or deleting a round."""
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    all_rounds = conn.execute(
        'SELECT * FROM rounds WHERE game_id = ? AND team1_actual IS NOT NULL ORDER BY round_number',
        (game_id,)
    ).fetchall()

    # Seed cumulative state from the round just before start_round_number
    team1_running_total = 0
    team2_running_total = 0
    team1_bags_total = 0
    team2_bags_total = 0

    for r in all_rounds:
        if r['round_number'] < start_round_number:
            team1_running_total = r['team1_total']
            team2_running_total = r['team2_total']
            team1_bags_total = r['team1_bags_total']
            team2_bags_total = r['team2_bags_total']

    # Now recalculate every round from start_round_number onwards
    for r in all_rounds:
        if r['round_number'] < start_round_number:
            continue

        t1_scoring = calculate_detailed_round_scoring(
            r['team1_bid'], r['team1_actual'], game,
            bool(r['team1_nil_success']), bool(r['team1_blind_nil_success']), bool(r['team1_blind_success'])
        )
        t2_scoring = calculate_detailed_round_scoring(
            r['team2_bid'], r['team2_actual'], game,
            bool(r['team2_nil_success']), bool(r['team2_blind_nil_success']), bool(r['team2_blind_success'])
        )

        t1_bags_earned = max(0, r['team1_actual'] - int(parse_bid(r['team1_bid'])[0]))
        t2_bags_earned = max(0, r['team2_actual'] - int(parse_bid(r['team2_bid'])[0]))

        t1_bags_before = team1_bags_total + t1_bags_earned
        t2_bags_before = team2_bags_total + t2_bags_earned

        team1_bags_total += t1_bags_earned
        team2_bags_total += t2_bags_earned

        t1_bag_penalty = 0
        t2_bag_penalty = 0
        while team1_bags_total >= game['bag_penalty_threshold']:
            t1_bag_penalty += game['bag_penalty_points']
            team1_bags_total -= game['bag_penalty_threshold']
        while team2_bags_total >= game['bag_penalty_threshold']:
            t2_bag_penalty += game['bag_penalty_points']
            team2_bags_total -= game['bag_penalty_threshold']

        t1_points = t1_scoring['total_points'] - t1_bag_penalty
        t2_points = t2_scoring['total_points'] - t2_bag_penalty

        team1_running_total += t1_points
        team2_running_total += t2_points

        conn.execute('''
            UPDATE rounds SET
                team1_points = ?, team2_points = ?,
                team1_total = ?, team2_total = ?,
                team1_bags_earned = ?, team2_bags_earned = ?,
                team1_bags_total = ?, team2_bags_total = ?,
                team1_bag_penalty = ?, team2_bag_penalty = ?,
                team1_bags_before_penalty = ?, team2_bags_before_penalty = ?,
                team1_bid_points = ?, team1_nil_bonus = ?, team1_blind_nil_bonus = ?,
                team1_blind_bonus = ?, team1_bag_points = ?,
                team2_bid_points = ?, team2_nil_bonus = ?, team2_blind_nil_bonus = ?,
                team2_blind_bonus = ?, team2_bag_points = ?
            WHERE id = ?
        ''', (
            t1_points, t2_points,
            team1_running_total, team2_running_total,
            t1_bags_earned, t2_bags_earned,
            team1_bags_total, team2_bags_total,
            t1_bag_penalty, t2_bag_penalty,
            t1_bags_before, t2_bags_before,
            t1_scoring['bid_points'], t1_scoring['nil_bonus'], t1_scoring['blind_nil_bonus'],
            t1_scoring['blind_bonus'], t1_scoring['bag_points'],
            t2_scoring['bid_points'], t2_scoring['nil_bonus'], t2_scoring['blind_nil_bonus'],
            t2_scoring['blind_bonus'], t2_scoring['bag_points'],
            r['id']
        ))

    # Update game-level totals and completion status
    last = conn.execute(
        'SELECT * FROM rounds WHERE game_id = ? AND team1_actual IS NOT NULL ORDER BY round_number DESC LIMIT 1',
        (game_id,)
    ).fetchone()

    if last:
        conn.execute('''
            UPDATE games SET team1_final_score = ?, team2_final_score = ?,
                             team1_bags = ?, team2_bags = ?
            WHERE id = ?
        ''', (last['team1_total'], last['team2_total'],
              last['team1_bags_total'], last['team2_bags_total'], game_id))

        # Re-evaluate completion
        if last['team1_total'] >= game['max_score'] or last['team2_total'] >= game['max_score']:
            if last['team1_total'] >= game['max_score']:
                winner = '{} & {}'.format(game['team1_player1'], game['team1_player2'])
            else:
                winner = '{} & {}'.format(game['team2_player1'], game['team2_player2'])
            conn.execute(
                "UPDATE games SET status = 'completed', winner = ?, completed_date = ? WHERE id = ?",
                (winner, datetime.now(), game_id)
            )
        else:
            # Game may have been completed before the edit — reopen it
            conn.execute(
                "UPDATE games SET status = 'active', winner = NULL, completed_date = NULL WHERE id = ? AND status = 'completed'",
                (game_id,)
            )
    else:
        # All rounds deleted — reset game totals
        conn.execute(
            'UPDATE games SET team1_final_score = 0, team2_final_score = 0, team1_bags = 0, team2_bags = 0, status = \'active\', winner = NULL, completed_date = NULL WHERE id = ?',
            (game_id,)
        )


@app.route('/game/<int:game_id>/round/<int:round_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_round(game_id, round_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?',
                        (game_id, session['user_id'])).fetchone()
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))

    round_data = conn.execute(
        'SELECT * FROM rounds WHERE id = ? AND game_id = ? AND team1_actual IS NOT NULL',
        (round_id, game_id)
    ).fetchone()
    if not round_data:
        flash('Round not found')
        conn.close()
        return redirect(url_for('game', game_id=game_id))

    if request.method == 'POST':
        team1_actual = int(request.form['team1_actual'])
        team2_actual = int(request.form['team2_actual'])

        if team1_actual + team2_actual != 13:
            flash('Team totals must equal 13')
            conn.close()
            return render_template('edit_round.html', game=game, round=round_data)

        team1_bid = request.form.get('team1_bid', round_data['team1_bid'])
        team2_bid = request.form.get('team2_bid', round_data['team2_bid'])

        team1_nil_success = request.form.get('team1_nil_success') == 'on'
        team1_blind_nil_success = request.form.get('team1_blind_nil_success') == 'on'
        team1_blind_success = request.form.get('team1_blind_success') == 'on'
        team2_nil_success = request.form.get('team2_nil_success') == 'on'
        team2_blind_nil_success = request.form.get('team2_blind_nil_success') == 'on'
        team2_blind_success = request.form.get('team2_blind_success') == 'on'

        # Update the raw data for this round; recalculate will handle derived fields
        conn.execute('''
            UPDATE rounds SET
                team1_bid = ?, team2_bid = ?,
                team1_actual = ?, team2_actual = ?,
                team1_nil_success = ?, team1_blind_nil_success = ?, team1_blind_success = ?,
                team2_nil_success = ?, team2_blind_nil_success = ?, team2_blind_success = ?
            WHERE id = ?
        ''', (team1_bid, team2_bid, team1_actual, team2_actual,
              team1_nil_success, team1_blind_nil_success, team1_blind_success,
              team2_nil_success, team2_blind_nil_success, team2_blind_success,
              round_id))

        recalculate_from_round(conn, game_id, round_data['round_number'])
        conn.commit()
        conn.close()
        flash('Round {} updated and scores recalculated.'.format(round_data['round_number']))
        return redirect(url_for('game', game_id=game_id))

    conn.close()
    return render_template('edit_round.html', game=game, round=round_data)


@app.route('/game/<int:game_id>/round/<int:round_id>/delete', methods=['POST'])
@require_login
def delete_round(game_id, round_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?',
                        (game_id, session['user_id'])).fetchone()
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))

    round_data = conn.execute(
        'SELECT * FROM rounds WHERE id = ? AND game_id = ? AND team1_actual IS NOT NULL',
        (round_id, game_id)
    ).fetchone()
    if not round_data:
        flash('Round not found')
        conn.close()
        return redirect(url_for('game', game_id=game_id))

    deleted_round_number = round_data['round_number']
    conn.execute('DELETE FROM rounds WHERE id = ?', (round_id,))

    # Re-number all subsequent rounds to close the gap
    conn.execute('''
        UPDATE rounds SET round_number = round_number - 1
        WHERE game_id = ? AND round_number > ?
    ''', (game_id, deleted_round_number))

    recalculate_from_round(conn, game_id, deleted_round_number)
    conn.commit()
    conn.close()
    flash('Round {} deleted and scores recalculated.'.format(deleted_round_number))
    return redirect(url_for('game', game_id=game_id))


@app.route('/game/<int:game_id>/abandon', methods=['POST'])
@require_login
def abandon_game(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?',
                        (game_id, session['user_id'])).fetchone()
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))

    conn.execute("UPDATE games SET status = 'abandoned' WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()

    flash('Game abandoned.')
    return redirect(url_for('dashboard'))


@app.route('/game/<int:game_id>/recover', methods=['POST'])
@require_login
def recover_game(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?',
                        (game_id, session['user_id'])).fetchone()
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))

    conn.execute("UPDATE games SET status = 'active' WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()

    flash('Game restored to active.')
    return redirect(url_for('game', game_id=game_id))


@app.route('/game/<int:game_id>/delete', methods=['POST'])
@require_login
def delete_game(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?',
                        (game_id, session['user_id'])).fetchone()
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))

    conn.execute('DELETE FROM rounds WHERE game_id = ?', (game_id,))
    conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()

    flash('Game permanently deleted.')
    return redirect(url_for('dashboard'))


@app.route('/games/bulk-abandon', methods=['POST'])
@require_login
def bulk_abandon_old_games():
    days = int(request.form.get('days', 30))
    cutoff = datetime.now() - timedelta(days=days)

    conn = get_db_connection()
    # Abandon active games with no round activity since the cutoff
    result = conn.execute('''
        UPDATE games
        SET status = 'abandoned'
        WHERE created_by_user_id = ?
          AND status = 'active'
          AND id NOT IN (
              SELECT DISTINCT game_id FROM rounds
              WHERE created_date >= ?
          )
          AND created_date < ?
    ''', (session['user_id'], cutoff, cutoff))

    abandoned_count = result.rowcount
    conn.commit()
    conn.close()

    flash('Abandoned {} stale game{} (no activity in {} days).'.format(
        abandoned_count, 's' if abandoned_count != 1 else '', days))
    return redirect(url_for('dashboard'))


@app.route('/game/<int:game_id>/rematch', methods=['POST'])
@require_login
def rematch(game_id):
    conn = get_db_connection()
    original = conn.execute(
        'SELECT * FROM games WHERE id = ? AND created_by_user_id = ?',
        (game_id, session['user_id'])
    ).fetchone()

    if not original:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))

    share_code = str(secrets.randbelow(90000) + 10000)

    cursor = conn.execute('''
        INSERT INTO games (
            created_by_user_id,
            team1_player1, team1_player2, team2_player1, team2_player2,
            max_score, nil_penalty, blind_nil_penalty,
            bag_penalty_threshold, bag_penalty_points, failed_nil_handling,
            share_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        original['team1_player1'], original['team1_player2'],
        original['team2_player1'], original['team2_player2'],
        original['max_score'], original['nil_penalty'], original['blind_nil_penalty'],
        original['bag_penalty_threshold'], original['bag_penalty_points'],
        original['failed_nil_handling'], share_code
    ))

    new_game_id = cursor.lastrowid
    conn.commit()
    conn.close()

    flash('Rematch started — same players, same rules, fresh scores!')
    return redirect(url_for('game', game_id=new_game_id))


@app.route('/game/<int:game_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_game(game_id):
    conn = get_db_connection()
    
    # Get game details
    game = conn.execute('SELECT * FROM games WHERE id = ? AND created_by_user_id = ?', 
                       (game_id, session['user_id'])).fetchone()
    
    if not game:
        flash('Game not found')
        conn.close()
        return redirect(url_for('dashboard'))
    
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
        
        # Update game settings
        conn.execute('''
            UPDATE games SET 
                team1_player1 = ?, team1_player2 = ?, team2_player1 = ?, team2_player2 = ?,
                max_score = ?, nil_penalty = ?, blind_nil_penalty = ?, bag_penalty_threshold = ?,
                bag_penalty_points = ?
            WHERE id = ?
        ''', (team1_player1, team1_player2, team2_player1, team2_player2,
              max_score, nil_penalty, blind_nil_penalty, bag_penalty_threshold,
              bag_penalty_points, game_id))
        
        conn.commit()
        conn.close()
        
        flash('Game settings updated successfully!')
        return redirect(url_for('game', game_id=game_id))
    
    conn.close()
    return render_template('edit_game.html', game=game)

if __name__ == '__main__':
    # For local development only
    app.run(host='0.0.0.0', port=5000, debug=True)