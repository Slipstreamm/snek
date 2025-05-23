# Snek - Discord Embedded Snake Game

A multiplayer Snake game that runs as a Discord bot application using Discord's embedded app functionality. Play in singleplayer mode against an AI opponent or challenge your friends in multiplayer mode!

## Features

- Classic Snake gameplay mechanics
- Singleplayer mode with AI opponent (three difficulty levels)
- Multiplayer mode for two Discord users
- Embedded directly within Discord using Discord's UI components
- Simple command interface for starting games and selecting modes
- Scoring system and win/lose conditions

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Discord account
- A Discord bot token

### Step 1: Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Snek")
3. Go to the "Bot" tab and click "Add Bot"
4. Under the "Privileged Gateway Intents" section, enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. Save your changes
6. Copy the bot token (you'll need this later)

### Step 2: Invite the Bot to Your Server

1. Go to the "OAuth2" tab in the Discord Developer Portal
2. In the "URL Generator" section, select the following scopes:
   - `bot`
   - `applications.commands`
3. Under "Bot Permissions", select:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Use Slash Commands
4. Copy the generated URL and open it in your browser
5. Select the server you want to add the bot to and authorize it

### Step 3: Set Up the Project

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/snek.git
   cd snek
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   APPLICATION_ID=your_application_id_here
   ```

### Step 4: Run the Bot

1. Start the bot:
   ```
   python main.py
   ```

2. Once the bot is running, you should see a message in the console indicating that it has logged in successfully.

## Usage

### Commands

- `/snek` - Start a new Snake game
  - Options:
    - `mode`: Choose between "singleplayer" and "multiplayer"
    - `difficulty`: Choose AI difficulty (for singleplayer mode) - "easy", "medium", or "hard"
- `/snek_help` - Show help information about the game

### Playing the Game

1. Use the `/snek` command in a Discord channel to start a new game
2. Use the arrow buttons in the embedded app to control your snake
3. In multiplayer mode, another user can join by clicking the "Join Game" button
4. Collect food to grow your snake and earn points
5. Avoid collisions with walls, other snakes, or yourself
6. The game ends when all snakes have collided, or in multiplayer mode, when only one snake remains

## Development

### Project Structure

```
snek/
├── main.py                 # Main entry point for the Discord bot
├── config.py               # Configuration settings
├── requirements.txt        # Project dependencies
├── game/
│   ├── __init__.py
│   ├── snake.py            # Snake game logic
│   ├── ai.py               # AI opponent logic
│   └── renderer.py         # Game rendering logic
├── discord_integration/
│   ├── __init__.py
│   ├── bot.py              # Discord bot setup and command handling
│   └── embedded_app.py     # Discord embedded app integration
└── README.md               # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper for Python
- [Pillow](https://python-pillow.org/) - Python Imaging Library
