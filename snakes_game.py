#!/usr/bin/python3

import cgi
import cgitb
import random
import json
import os
import urllib.parse

# Enable CGI error reporting for debugging
cgitb.enable()

# Print Content-Type header (required for CGI)
print("Content-Type: text/html")
print()  # Empty line required after headers

# Game configuration
SNAKES_AND_LADDERS = {
    # Snakes (higher to lower positions)
    16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78,
    # Ladders (lower to higher positions)
    1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100
}

# Session storage using a simple file system
SESSION_DIR = '/tmp'
SESSION_FILE = os.path.join(SESSION_DIR, 'snakes_ladders_game.json')

def load_game_state():
    """Load the current game state from file storage"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError):
        pass
    
    # Return default game state if file doesn't exist or is corrupted
    return {
        'players': {'Player 1': 0, 'Player 2': 0},
        'current_player': 'Player 1',
        'message': 'Welcome to Snakes and Ladders! Click "Roll Dice" to start.',
        'game_over': False,
        'winner': None
    }

def save_game_state(state):
    """Save the current game state to file storage"""
    try:
        # Ensure the directory exists
        os.makedirs(SESSION_DIR, exist_ok=True)
        with open(SESSION_FILE, 'w') as f:
            json.dump(state, f)
    except IOError:
        # If we can't save, continue anyway (game will reset on next visit)
        pass

def roll_dice_action(game_state):
    """Handle the dice roll logic"""
    if game_state['game_over']:
        return game_state
    
    current_player = game_state['current_player']
    roll = random.randint(1, 6)
    current_position = game_state['players'][current_player]
    new_position = current_position + roll
    
    # Check if player would go over 100
    if new_position > 100:
        game_state['message'] = f"{current_player} rolled a {roll}. Cannot move - need exact roll to reach 100!"
        # Don't switch players, give them another chance
        return game_state
    
    # Move to new position
    final_position = new_position
    
    # Check for snakes and ladders
    if new_position in SNAKES_AND_LADDERS:
        final_position = SNAKES_AND_LADDERS[new_position]
        
        if final_position > new_position:
            # It's a ladder
            game_state['message'] = f"{current_player} rolled a {roll} and landed on square {new_position}. 🪜 LADDER! Climb up to {final_position}!"
        else:
            # It's a snake
            game_state['message'] = f"{current_player} rolled a {roll} and landed on square {new_position}. 🐍 SNAKE! Slide down to {final_position}!"
    else:
        # Normal move
        game_state['message'] = f"{current_player} rolled a {roll}. Moved from {current_position} to {final_position}."
    
    # Update player position
    game_state['players'][current_player] = final_position
    
    # Check for winner
    if final_position == 100:
        game_state['message'] = f"🎉 CONGRATULATIONS! {current_player} has won the game! 🎉"
        game_state['game_over'] = True
        game_state['winner'] = current_player
        return game_state
    
    # Switch to next player
    game_state['current_player'] = 'Player 2' if current_player == 'Player 1' else 'Player 1'
    
    return game_state

def reset_game():
    """Reset the game to initial state"""
    return {
        'players': {'Player 1': 0, 'Player 2': 0},
        'current_player': 'Player 1',
        'message': 'New game started! Player 1 goes first.',
        'game_over': False,
        'winner': None
    }

def generate_board_html(game_state):
    """Generate HTML representation of the game board"""
    board_html = '<div class="board">'
    
    # Create 10x10 grid, numbered 100 to 1 (top to bottom)
    for row in range(9, -1, -1):  # 9 to 0 (rows 10 to 1)
        board_html += '<div class="board-row">'
        
        # Alternate direction for snake-and-ladder board pattern
        if row % 2 == 1:
            # Odd rows: left to right (1-10, 21-30, 41-50, 61-70, 81-90)
            col_range = range(10)
        else:
            # Even rows: right to left (11-20, 31-40, 51-60, 71-80, 91-100)
            col_range = range(9, -1, -1)
        
        for col in col_range:
            square_num = row * 10 + col + 1
            
            # Determine square class and content
            square_class = "square"
            title_text = f"Square {square_num}"
            
            # Check if it's a snake or ladder
            if square_num in SNAKES_AND_LADDERS:
                destination = SNAKES_AND_LADDERS[square_num]
                if destination > square_num:
                    square_class += " ladder"
                    title_text += f" - Ladder to {destination}"
                else:
                    square_class += " snake"
                    title_text += f" - Snake to {destination}"
            
            # Check if players are on this square
            players_here = []
            for player, position in game_state['players'].items():
                if position == square_num:
                    players_here.append(player)
                    square_class += " occupied"
            
            # Add player indicators
            player_indicators = ""
            if players_here:
                player_indicators = f" {'P1' if 'Player 1' in players_here else ''}{'P2' if 'Player 2' in players_here else ''}"
            
            board_html += f'<div class="{square_class}" title="{title_text}">{square_num}{player_indicators}</div>'
        
        board_html += '</div>'
    
    board_html += '</div>'
    return board_html

def generate_html(game_state):
    """Generate the complete HTML page"""
    
    # Get current script name for form actions
    script_name = os.environ.get('SCRIPT_NAME', '/cgi-bin/snakes_game.py')
    
    board_html = generate_board_html(game_state)
    
    # Determine if roll button should be disabled
    roll_disabled = 'disabled' if game_state['game_over'] else ''
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐍 Snakes and Ladders 🪜</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        h1 {{
            text-align: center;
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        
        .message {{
            background: #e8f6f3;
            border: 2px solid #1abc9c;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
        }}
        
        .game-over {{
            background: #fff3cd;
            border-color: #f39c12;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
            100% {{ transform: scale(1); }}
        }}
        
        .players-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 30px 0;
        }}
        
        .player-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 3px solid #dee2e6;
            transition: all 0.3s ease;
        }}
        
        .player-card.current {{
            background: #d1ecf1;
            border-color: #17a2b8;
            transform: scale(1.05);
        }}
        
        .player-name {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #495057;
        }}
        
        .player-position {{
            font-size: 2.5em;
            font-weight: bold;
            color: #e74c3c;
        }}
        
        .controls {{
            text-align: center;
            margin: 30px 0;
        }}
        
        button {{
            font-size: 1.2em;
            padding: 12px 25px;
            margin: 0 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .roll-btn {{
            background: #27ae60;
            color: white;
        }}
        
        .roll-btn:hover:not(:disabled) {{
            background: #219a52;
            transform: translateY(-2px);
        }}
        
        .roll-btn:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
        }}
        
        .reset-btn {{
            background: #e74c3c;
            color: white;
        }}
        
        .reset-btn:hover {{
            background: #c0392b;
            transform: translateY(-2px);
        }}
        
        .board {{
            margin: 30px auto;
            max-width: 600px;
            background: #2c3e50;
            padding: 10px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}
        
        .board-row {{
            display: flex;
        }}
        
        .square {{
            flex: 1;
            aspect-ratio: 1;
            background: #3498db;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
            margin: 1px;
            border-radius: 3px;
            position: relative;
        }}
        
        .square.snake {{
            background: #e74c3c;
        }}
        
        .square.ladder {{
            background: #27ae60;
        }}
        
        .square.occupied {{
            box-shadow: inset 0 0 0 3px #f39c12;
            animation: glow 2s infinite;
        }}
        
        @keyframes glow {{
            0%, 100% {{ box-shadow: inset 0 0 0 3px #f39c12; }}
            50% {{ box-shadow: inset 0 0 0 3px #e67e22, 0 0 10px #f39c12; }}
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .legend-square {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐍 Snakes and Ladders 🪜</h1>
        
        <div class="message {'game-over' if game_state['game_over'] else ''}">
            {game_state['message']}
        </div>
        
        <div class="players-section">
            <div class="player-card {'current' if game_state['current_player'] == 'Player 1' and not game_state['game_over'] else ''}">
                <div class="player-name">🔴 Player 1</div>
                <div class="player-position">{game_state['players']['Player 1']}</div>
            </div>
            <div class="player-card {'current' if game_state['current_player'] == 'Player 2' and not game_state['game_over'] else ''}">
                <div class="player-name">🔵 Player 2</div>
                <div class="player-position">{game_state['players']['Player 2']}</div>
            </div>
        </div>
        
        <div class="controls">
            <form method="post" action="{script_name}" style="display: inline;">
                <button type="submit" name="action" value="roll" class="roll-btn" {roll_disabled}>
                    🎲 Roll Dice
                </button>
            </form>
            
            <form method="post" action="{script_name}" style="display: inline;">
                <button type="submit" name="action" value="reset" class="reset-btn">
                    🔄 New Game
                </button>
            </form>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-square" style="background: #3498db;"></div>
                <span>Normal Square</span>
            </div>
            <div class="legend-item">
                <div class="legend-square" style="background: #27ae60;"></div>
                <span>🪜 Ladder</span>
            </div>
            <div class="legend-item">
                <div class="legend-square" style="background: #e74c3c;"></div>
                <span>🐍 Snake</span>
            </div>
            <div class="legend-item">
                <div class="legend-square" style="background: #3498db; box-shadow: inset 0 0 0 2px #f39c12;"></div>
                <span>Player Position</span>
            </div>
        </div>
        
        {board_html}
        
        <div style="margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
            <p><strong>How to Play:</strong></p>
            <p>🎲 Click "Roll Dice" to move your piece<br>
            🪜 Ladders take you up, 🐍 Snakes take you down<br>
            🏆 First player to reach square 100 wins!</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html

def main():
    """Main CGI application logic"""
    # Parse form data
    form = cgi.FieldStorage()
    action = form.getvalue('action', '')
    
    # Load current game state
    game_state = load_game_state()
    
    # Process the action
    if action == 'roll':
        game_state = roll_dice_action(game_state)
    elif action == 'reset':
        game_state = reset_game()
    
    # Save the updated game state
    save_game_state(game_state)
    
    # Generate and output the HTML page
    html = generate_html(game_state)
    print(html)

# Run the main application
if __name__ == '__main__':
    main()