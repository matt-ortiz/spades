# Spades Score Keeper - Product Requirements Document
## Version 1.3 - Mobile-First UI and Simplified Bid Format

## Overview
A lightweight web application for tracking scores in Spades card games, built with Python. Features simple game creation with any player names, automatic score calculation, and game history. **No user data tracking or management overhead** - just create games and play.

## Core Features

### User Management
- **Registration**: Users create accounts with name and email
- **Authentication**: Email-based security code system using SMTP2GO
- **Simple Login**: Enter email, receive security code, enter code to access

### Game Setup
- **Team Configuration**: 
  - Team 1: Two text input fields for player names
  - Team 2: Two text input fields for player names
- **Game Rules Configuration**:
  - Max Score setting (default: 500)
  - Nil penalty (default: 100 points)
  - Blind nil penalty (default: 200 points)
  - **Bag penalty settings**: 10 bags = -100 points (configurable)
  - **Failed nil handling**: 
    - "Takes Bags" (default) - Failed nil tricks count as bags
    - "Helps Team" - Failed nil tricks help partner's bid
    - "No Effect" - Failed nil tricks ignored
- **New Game**: Start fresh game with entered player names

### Score Tracking
- **Team Bid Entry**: 
  - Team bid modal with large touch buttons (1-13, skip 0 as it's pointless)
  - Optional checkboxes for "Nil" and "Blind Nil" modifiers
  - Confirmation button shows selected bid: **"[Team Name] bid: 6"** (green when ready, gray when disabled)
  - Bid format stored as: "7", "4b", "5bn" (number + modifier)
- **Actual Score Entry**:
  - Team 1 actual tricks taken (0-13) - large button interface
  - Team 2 actual tricks taken (0-13) - large button interface  
  - Validation: Team totals must equal 13
- **Automatic Calculation**:
  - Parse team bid strings to calculate points
  - Handle standard, nil, and blind nil combinations
  - Track running totals
  - Determine round winner
- **Round Management**:
  - Edit last round (mistakes happen frequently)
  - Clear visual feedback on data entry
  - Auto-save rounds to prevent data loss

### Game Management
- **Current Game View**: Display current scores, round history, edit last round
- **Game Completion**: Detect when max score is reached
- **Game History**: View past completed games (session-based, no user tracking)
- **Game Abandonment**: Option to delete/abandon incomplete games

## Critical V1 Features

### Input Validation & Error Handling
- **Bid Validation**: 1-13 with nil/blind nil modifiers (skip 0 as pointless)
- **Score Validation**: Actual scores 0-13, team totals must equal 13
- **Email Validation**: Proper format checking
- **Graceful Error Handling**: Clear error messages, no crashes
- **Data Integrity**: Prevent duplicate round entry, validate before saving

### Mobile-First Design
- **Large Touch Buttons**: Primary interface uses big, tappable buttons (1-13)
- **Touch-Friendly Modals**: Bid entry in modal with clear confirmation buttons
- **Visual State Management**: Green confirmation buttons when ready, gray when disabled
- **Portrait Layout**: Optimized for vertical phone use
- **Readable Typography**: Clear numbers and game state indicators

### User Experience Enhancements
- **Edit Last Round**: Fix scoring mistakes (common in card games)
- **Auto-Save**: Rounds saved immediately, no data loss on refresh
- **Visual Feedback**: Loading states, success confirmations
- **Keyboard Navigation**: Enter key submission, tab navigation
- **Clear Game Status**: Visual indicators of game phase and current scores

## Technical Requirements

### Backend
- **Framework**: Python (Flask recommended for simplicity)
- **Database**: SQLite for lightweight storage
- **Session Management**: Simple session-based auth, no user data tracking
- **Key Tables**:
  - Users (id, name, email, created_date, last_login) - minimal data
  - Auth_codes (id, user_id, code, expires_at, used)
  - Games (id, created_by_user_id, team1_player1, team1_player2, team2_player1, team2_player2, max_score, nil_penalty_rule, blind_nil_penalty_rule, status, created_date, completed_date)
  - Rounds (id, game_id, round_number, team1_bid, team2_bid, team1_actual, team2_actual, team1_points, team2_points, team1_total, team2_total, team1_nil_type, team2_nil_type)

### Frontend
- **Mobile-First Design**: Responsive, touch-friendly interface
- **Simple HTML/CSS/JavaScript**: Basic responsive design optimized for phones
- **Key Pages**:
  - Home/Dashboard
  - New Game Setup
  - Active Game Score Entry (primary interface)
  - Game History
  - Rules Settings
- **Performance**: Lightweight pages, minimal JavaScript, fast loading

## User Stories

### As a player, I want to:
1. Register with my name and email address (minimal data collection)
2. Receive a security code via email to log in
3. Start a new game by typing in 4 player names (any names)
4. Set game rules (max score, nil penalties, blind nil penalties) before starting
5. Enter team bids using touch-friendly modal with large buttons (1-13 + modifiers)
6. Confirm bids with clear visual feedback: "[Team Name] bid: 6"
6. Enter actual scores with validation (totals must equal 13)
7. See calculated points automatically with clear visual feedback
8. Edit the last round if I made a mistake
9. View the current game status and running totals clearly
10. See when a game is complete (team reaches max score)
11. Review history of games from my current session
12. Have the app work reliably on my phone during games

### As a scorekeeper, I want to:
1. Have a clean, simple interface for rapid score entry
2. See clear visual indication of current scores and progress
3. Have the math calculated automatically to avoid errors
4. Be able to review previous rounds if needed

## Game Logic Requirements

### Scoring Rules
- **Standard Scoring**: 10 points per bid + 1 point per overtrick
- **Failed Bid**: -10 points per trick short of bid
- **Nil Bid Success**: 100 points (configurable)
- **Nil Bid Failure**: -100 points (configurable)
- **Blind Nil Success**: 200 points (configurable)
- **Blind Nil Failure**: -200 points (configurable)
- **Bags**: Track overtricks, penalty when threshold reached (default: 10 bags = -100 points)
- **Failed Nil Bag Handling** (configurable):
  - **Takes Bags** (default): Failed nil tricks count as bags
  - **Helps Team**: Failed nil tricks help partner meet bid
  - **No Effect**: Failed nil tricks ignored completely

### Game Flow
1. Enter team names
2. Set rules (max score, nil penalties, blind nil penalties, bag rules, failed nil handling)
3. For each round:
   - Open bid modal for each team with large touch buttons (1-13)
   - Select nil/blind modifiers if needed
   - Confirm with green button showing "[Team Name] bid: 6" 
   - Enter actual tricks taken using large button interface
   - Validate: team totals must equal 13
   - Calculate and display points automatically
   - Update running totals
   - Auto-save round data
   - Check for game completion
4. Option to edit last round if mistakes were made
5. Display winner when max score reached

## Deployment
- **Platform**: PythonAnywhere (free tier suitable for this application)
- **Email Service**: SMTP2GO for security code delivery
- **Database**: SQLite (included with PythonAnywhere)
- **Framework**: Flask with minimal dependencies for easy deployment

## Authentication Flow
1. User enters name and email on registration
2. System generates 6-digit security code, stores in database with expiration
3. Code sent via SMTP2GO to user's email
4. User enters code to complete login
5. Session maintained for reasonable duration
6. Codes expire after 15 minutes and are single-use
- Export game history to CSV
- Basic statistics (win/loss records per player)
- Mobile-responsive design
- Undo last round functionality
- Tournament mode for multiple games

## Nice-to-Have Features (Future Enhancements)

### Database Schema
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Auth codes table
CREATE TABLE auth_codes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Games table
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

-- Rounds table
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

### Bid Format Parsing
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

### Key Routes
- `/` - Home dashboard (requires login)
- `/register` - User registration form
- `/login` - Email entry for security code
- `/verify` - Security code verification
- `/new-game` - Game setup form
- `/game/<id>` - Active game interface (primary page)
- `/game/<id>/round` - Round entry form
- `/game/<id>/edit-round/<round_num>` - Edit last round
- `/game/<id>/delete` - Abandon game
- `/history` - User's game history (session-based)
- `/settings` - Rules configuration
- `/logout` - Clear session

## Data Philosophy
- Ability to complete a full game without errors
- Fast round entry (under 30 seconds per round)
- Accurate score calculation including nil/blind nil scenarios
- Reliable game history storage (session-based)
- Mobile-friendly interface that works during actual card games
- Error-free bid validation and data entry
- Successful email delivery for authentication codes

## UI/UX Flow for Bid Entry

### Bid Modal Design
1. **Team Selection**: Tap "Enter Bid" for Team 1 or Team 2
2. **Number Selection**: Large buttons 1-13 (skip 0 as pointless)
3. **Modifier Options**: Checkboxes for "Nil" and "Blind Nil" 
4. **Visual Feedback**: Selected number highlights, modifiers show clearly
5. **Confirmation**: Green button shows **"[Matt/Kellie] bid: 6"** when ready
6. **Disabled State**: Gray button when no selection made
7. **Display Format**: Store as "6", "4b", "5bn" but display as "6", "4 + Blind", "5 + Blind Nil"

### Actual Score Entry
1. **Large Button Grid**: 0-13 for each team's actual tricks
2. **Real-time Validation**: Show error if totals don't equal 13
3. **Visual Confirmation**: Clear display of selected scores
4. **Auto-calculation**: Points calculated and displayed immediately
**Minimal Data Collection**: This app intentionally avoids extensive user data tracking and management. Users create simple accounts for session management only. Game history is accessible during sessions but no long-term user analytics or data mining. The focus is on the game, not data collection.