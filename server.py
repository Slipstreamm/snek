import os
from flask import Flask, send_from_directory, request, jsonify, redirect, url_for
from flask_cors import CORS
import config

app = Flask(__name__, static_folder='web')
CORS(app)  # Enable CORS for all routes

# Get the base URL from config or environment
BASE_URL = config.EMBEDDED_APP_URL

@app.route('/')
def index():
    """Serve the main HTML file."""
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory('web', path)

@app.route('/api/config')
def get_config():
    """Return configuration for the client."""
    return jsonify({
        'clientId': config.APPLICATION_ID,
        'gridSize': config.GRID_SIZE,
        'cellSize': config.CELL_SIZE,
        'fps': config.FPS,
        'baseUrl': BASE_URL,
        'colors': {
            'black': config.BLACK,
            'white': config.WHITE,
            'green': config.GREEN,
            'red': config.RED,
            'blue': config.BLUE,
            'yellow': config.YELLOW
        }
    })

@app.route('/api/token', methods=['POST'])
def exchange_token():
    """Exchange authorization code for access token."""
    # In a real application, you would exchange the code for a token
    # using Discord's OAuth2 API
    data = request.json
    code = data.get('code')

    # For this example, we'll just return a simulated token
    # In a real app, you would make a request to Discord's token endpoint
    return jsonify({
        'access_token': 'simulated_token',
        'token_type': 'Bearer',
        'expires_in': 604800
    })

@app.route('/discord-activity')
def discord_activity():
    """Special route for Discord Activity."""
    # Get parameters from the request
    mode = request.args.get('mode', 'singleplayer')
    difficulty = request.args.get('difficulty', 'medium')

    # Redirect to the main app with parameters
    return redirect(f'/?mode={mode}&difficulty={difficulty}&is_activity=true')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)
