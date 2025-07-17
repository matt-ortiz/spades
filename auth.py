import os
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash
from models import get_db_connection

def send_security_code(email, code):
    """Send security code via SMTP2GO"""
    api_key = os.environ.get('SMTP2GO_API_KEY')
    
    if not api_key:
        # Development mode - just print the code
        print(f"DEVELOPMENT: Security code for {email}: {code}")
        return True
    
    url = "https://api.smtp2go.com/v3/email/send"
    
    data = {
        "api_key": api_key,
        "to": [email],
        "sender": "matt@mattortiz.net",
        "subject": "Your Spades Score Keeper Login Code",
        "text_body": f"Your security code is: {code}\n\nThis code will expire in 15 minutes.",
        "html_body": f"""
        <html>
        <body>
            <h2>Your Spades Score Keeper Login Code</h2>
            <p>Your security code is: <strong>{code}</strong></p>
            <p>This code will expire in 15 minutes.</p>
        </body>
        </html>
        """
    }
    
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_security_code(user_id, code):
    """Verify security code and mark as used"""
    conn = get_db_connection()
    
    # Find valid, unused code
    auth_code = conn.execute('''
        SELECT * FROM auth_codes 
        WHERE user_id = ? AND code = ? AND used = FALSE AND expires_at > ?
        ORDER BY created_date DESC LIMIT 1
    ''', (user_id, code, datetime.now())).fetchone()
    
    if auth_code:
        # Mark code as used
        conn.execute('UPDATE auth_codes SET used = TRUE WHERE id = ?', (auth_code['id'],))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def require_login(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function