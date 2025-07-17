# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Spades Score Keeper web application built with Python Flask. The project is currently in the planning phase with detailed PRD documentation but no implementation code yet. **Version 1.3** focuses on mobile-first UI with configurable bag penalties and failed nil handling for comprehensive Spades rule support.

**Note**: This repository currently contains only Product Requirements Documents (PRDs) and no actual implementation code. The project needs to be built from scratch based on the specifications in the PRD files.

## Project Structure (To Be Implemented)

Based on the PRD, the final project structure should be:

```
spades-scorekeeper/
├── app.py                 # Main Flask application
├── models.py             # Database models and schema
├── auth.py               # Authentication logic
├── scoring.py            # Spades scoring calculations
├── email_service.py      # SMTP2GO integration
├── requirements.txt      # Python dependencies
├── database.db          # SQLite database (created at runtime)
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── app.js        # Frontend JavaScript
├── templates/
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── verify.html       # Code verification
│   ├── dashboard.html    # Main dashboard
│   ├── new_game.html     # New game setup
│   ├── game.html         # Active game interface
│   └── history.html      # Game history
└── CLAUDE.md            # This file
```

## Technology Stack

- **Backend**: Python Flask framework
- **Database**: SQLite (lightweight, file-based)
- **Frontend**: HTML, CSS, JavaScript (simple, responsive)
- **Authentication**: Email-based security codes via SMTP2GO
- **Deployment**: PythonAnywhere free tier

## Core Application Architecture

### Database Schema
The application uses SQLite with 4 main tables:
- `users` - User accounts (name, email, timestamps) - minimal data collection
- `auth_codes` - Security codes for email authentication
- `games` - Game instances with player names, settings, and blind nil support
- `rounds` - Individual rounds with per-player bids, nil types, and validation

### Authentication Flow
1. User registration with name and email
2. Security code generation and email delivery via SMTP2GO
3. Code verification and session creation
4. Session-based authentication for protected routes

### Game Flow
1. User creates new game with 4 player names
2. Configurable rules (max score, nil penalties)
3. Round-by-round bid entry and score calculation
4. Automatic point calculation based on Spades rules
5. Game completion detection when max score reached

### Spades Scoring Rules
- Standard scoring: 10 points per bid + 1 point per overtrick
- Failed bid: -10 points per trick short of bid
- Nil bid success: 100 points (configurable)
- Nil bid failure: -100 points (configurable)
- Blind nil success: 200 points (configurable)
- Blind nil failure: -200 points (configurable)
- Bags: Track overtricks, penalty when threshold reached (default: 10 bags = -100 points)
- Failed nil bag handling (configurable):
  - Takes bags (default): Failed nil tricks count as bags
  - Helps team: Failed nil tricks help partner meet bid
  - No effect: Failed nil tricks ignored completely

## Key Routes (To Be Implemented)

- `/` - Dashboard (requires login)
- `/register` - User registration form
- `/login` - Email entry for security code
- `/verify` - Security code verification
- `/logout` - Clear session
- `/new-game` - Game setup form
- `/game/<id>` - Active game interface (primary page)
- `/game/<id>/round` - Add new round
- `/game/<id>/edit-round/<round_num>` - Edit last round
- `/game/<id>/delete` - Abandon game
- `/history` - User's game history (session-based)
- `/settings` - Rules configuration

## Development Commands

Since this is a Flask application, once implemented, common commands will be:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
# or
flask run

# Initialize database (custom command to be implemented)
python -c "from models import init_db; init_db()"
```

## Environment Variables Required

```bash
SMTP2GO_API_KEY=your_smtp2go_api_key
SECRET_KEY=your_flask_secret_key
FLASK_ENV=development  # or production
```

## Development Priorities

1. **Phase 1**: Basic Flask app setup, database models, user registration/login
2. **Phase 2**: Game creation, basic score entry and calculation
3. **Phase 3**: Game history, improved UI/UX
4. **Phase 4**: Advanced features (rule configuration, game completion)

## Critical V1 Features

### Mobile-First Design
- **Large Touch Buttons**: Primary interface uses big, tappable buttons (1-13 for bids)
- **Touch-Friendly Modals**: Bid entry in modal with clear confirmation buttons
- **Visual State Management**: Green confirmation buttons when ready, gray when disabled
- **Portrait Layout**: Optimized for vertical phone use during actual card games
- **Readable Typography**: Clear numbers and game state indicators

### Input Validation & Error Handling
- **Bid validation**: 1-13 with nil/blind nil modifiers (skip 0 as pointless)
- **Score validation**: Actual scores 0-13, team totals must equal 13
- **Email validation**: Proper format checking
- **Data integrity**: Prevent duplicate round entry, validate before saving
- **Graceful error handling**: Clear error messages, no crashes

### User Experience Enhancements
- **Edit last round**: Fix scoring mistakes (common in card games)
- **Auto-save**: Rounds saved immediately, no data loss on refresh
- **Visual feedback**: Loading states, success confirmations
- **Keyboard navigation**: Enter key submission, tab navigation
- **Clear game status**: Visual indicators of game phase and current scores

## Implementation Notes

- Use SQLite for simplicity and PythonAnywhere compatibility
- **Mobile-first responsive design** - primary interface for phones
- Focus on fast, intuitive score entry interface optimized for touch
- Automatic calculation of complex Spades scoring rules including blind nil
- Session-based authentication with email security codes
- **Minimal data collection philosophy** - simple accounts, session-based history
- Target deployment on PythonAnywhere free tier

## Files in Repository

- `spades_scorekeeper_prd.md` - Main product requirements document
- `spades_scorekeeper_prd copy.md` - Backup copy of PRD

## Updated Database Schema (V1.3)

The rounds table now includes bag tracking:

```sql
CREATE TABLE rounds (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    team1_bid TEXT NOT NULL, -- Examples: "7", "4b", "5bn"
    team2_bid TEXT NOT NULL, -- Examples: "6", "4b", "5bn" 
    team1_actual INTEGER NOT NULL,
    team2_actual INTEGER NOT NULL,
    team1_points INTEGER NOT NULL,
    team2_points INTEGER NOT NULL,
    team1_total INTEGER NOT NULL,
    team2_total INTEGER NOT NULL,
    team1_bags_earned INTEGER DEFAULT 0,
    team2_bags_earned INTEGER DEFAULT 0,
    team1_bags_total INTEGER DEFAULT 0,
    team2_bags_total INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games (id)
);
```

Games table includes comprehensive rule configuration:
```sql
CREATE TABLE games (
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
    failed_nil_handling TEXT DEFAULT 'takes_bags', -- 'takes_bags', 'helps_team', 'no_effect'
    status TEXT DEFAULT 'active',
    team1_final_score INTEGER DEFAULT 0,
    team2_final_score INTEGER DEFAULT 0,
    team1_bags INTEGER DEFAULT 0,
    team2_bags INTEGER DEFAULT 0,
    winner TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users (id)
);
```

## Bid Format System (V1.3)

### Bid String Format
- **Regular bid**: "7" (just the number)
- **Blind bid**: "4b" (number + 'b')
- **Nil bid**: "0n" (0 + 'n')  
- **Blind nil**: "0bn" (0 + 'bn')

### Bid Parsing Logic
```python
def parse_bid(bid_string):
    """Parse bid string format: '7', '4b', '5bn'"""
    if bid_string.endswith('bn'):
        return int(bid_string[:-2]), 'blind_nil'
    elif bid_string.endswith('b'):
        return int(bid_string[:-1]), 'blind'  
    elif bid_string.endswith('n'):
        return int(bid_string[:-1]), 'nil'
    else:
        return int(bid_string), 'regular'
```

## Bag Penalty System (V1.3)

### Configurable Bag Rules
- **Bag penalty threshold**: Default 10 bags (configurable)
- **Bag penalty points**: Default -100 points (configurable)
- **Failed nil handling**: Three options for how failed nil tricks are handled:
  1. **Takes bags** (default): Failed nil tricks count as bags for the team
  2. **Helps team**: Failed nil tricks help partner meet their bid
  3. **No effect**: Failed nil tricks are ignored completely

### Bag Tracking Logic
- Each round tracks bags earned and running bag totals
- Penalty applied when bag threshold is reached
- Bag counts reset after penalty is applied
- Failed nil handling affects bag calculation based on game configuration

## Mobile UI Flow (V1.3)

### Bid Entry Modal Design
1. **Team Selection**: Tap "Enter Bid" for Team 1 or Team 2
2. **Number Selection**: Large buttons 1-13 (skip 0 as pointless)
3. **Modifier Options**: Checkboxes for "Nil" and "Blind Nil" 
4. **Visual Feedback**: Selected number highlights, modifiers show clearly
5. **Confirmation**: Green button shows **"[Team Name] bid: 6"** when ready
6. **Disabled State**: Gray button when no selection made
7. **Display Format**: Store as "6", "4b", "5bn" but display as "6", "4 + Blind", "5 + Blind Nil"

### Actual Score Entry
1. **Large Button Grid**: 0-13 for each team's actual tricks
2. **Real-time Validation**: Show error if totals don't equal 13
3. **Visual Confirmation**: Clear display of selected scores
4. **Auto-calculation**: Points calculated and displayed immediately

## Data Philosophy

**Minimal Data Collection**: This app intentionally avoids extensive user data tracking and management. Users create simple accounts for session management only. Game history is accessible during sessions but no long-term user analytics or data mining. The focus is on the game, not data collection.

**Status**: This project is in planning phase. All implementation needs to be done based on the detailed specifications in the PRD files.