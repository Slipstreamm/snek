import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
GUILD_ID = os.getenv('GUILD_ID')  # Optional: For development in a specific server

# Embedded App Configuration
EMBEDDED_APP_URL = os.getenv('EMBEDDED_APP_URL', 'http://localhost:5010')  # Default to localhost for development

# Game Configuration
GRID_SIZE = 20  # Size of the game grid (20x20)
CELL_SIZE = 20  # Size of each cell in pixels
GAME_WIDTH = GRID_SIZE * CELL_SIZE
GAME_HEIGHT = GRID_SIZE * CELL_SIZE
FPS = 10  # Frames per second / game speed

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Game Modes
SINGLEPLAYER = 'singleplayer'
MULTIPLAYER = 'multiplayer'

# AI Difficulty Levels
AI_EASY = 'easy'
AI_MEDIUM = 'medium'
AI_HARD = 'hard'
