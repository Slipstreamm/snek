import os
from flask import Flask, send_from_directory, request, jsonify, redirect, url_for
from flask_cors import CORS
import config

app = Flask(__name__, static_folder='web')
CORS(app)  # Enable CORS for all routes

# Get the base URL from config or environment
BASE_URL = config.EMBEDDED_APP_URL

@app.route('/', strict_slashes=False)
def index():
    """Serve the main HTML file."""
    return send_from_directory('web', 'index.html')

@app.route('/snake-game', strict_slashes=False)
def snake_game():
    """Alias for the main HTML file to support legacy URLs."""
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

    # Log the code for debugging
    print(f"Received authorization code: {code}")

    # For this example, we'll just return a simulated token
    # In a real app, you would make a request to Discord's token endpoint
    # using the code to get a real access token
    return jsonify({
        'access_token': f'simulated_token_{code[:8] if code else "no_code"}',
        'token_type': 'Bearer',
        'expires_in': 604800
    })

@app.route('/discord-activity', strict_slashes=False)
def discord_activity():
    """Special route for Discord Activity."""
    # Get parameters from the request
    mode = request.args.get('mode', 'singleplayer')
    difficulty = request.args.get('difficulty', 'medium')

    # Get Discord-specific parameters
    guild_id = request.args.get('guild_id')
    channel_id = request.args.get('channel_id')
    activity_id = request.args.get('activity_id')
    instance_id = request.args.get('instance_id')
    location_id = request.args.get('location_id')
    launch_id = request.args.get('launch_id')
    referrer_id = request.args.get('referrer_id')
    custom_id = request.args.get('custom_id')
    frame_id = request.args.get('frame_id')
    platform = request.args.get('platform')

    # Log all parameters for debugging
    print(f"Discord Activity Request: {request.args}")

    # Build the query parameters
    query_params = {
        'mode': mode,
        'difficulty': difficulty,
        'is_activity': 'true'
    }

    # Add Discord-specific parameters if available
    if guild_id:
        query_params['guild_id'] = guild_id
    if channel_id:
        query_params['channel_id'] = channel_id
    if activity_id:
        query_params['activity_id'] = activity_id
    if instance_id:
        query_params['instance_id'] = instance_id
    if location_id:
        query_params['location_id'] = location_id
    if launch_id:
        query_params['launch_id'] = launch_id
    if referrer_id:
        query_params['referrer_id'] = referrer_id
    if custom_id:
        query_params['custom_id'] = custom_id
    if frame_id:
        query_params['frame_id'] = frame_id
    if platform:
        query_params['platform'] = platform

    # Build the query string
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])

    # Redirect to the main app with parameters
    return redirect(f'/?{query_string}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)
