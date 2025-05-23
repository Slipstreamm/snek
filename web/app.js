// Game configuration
const GRID_SIZE = 20;
const CELL_SIZE = 20;
const GAME_WIDTH = GRID_SIZE * CELL_SIZE;
const GAME_HEIGHT = GRID_SIZE * CELL_SIZE;
const FPS = 10;

// Colors
const BLACK = '#000000';
const WHITE = '#FFFFFF';
const GREEN = '#00FF00';
const RED = '#FF0000';
const BLUE = '#0000FF';
const YELLOW = '#FFFF00';

// Game elements
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const playerScoreElement = document.getElementById('player-score');
const aiScoreElement = document.getElementById('ai-score');
const gameStatusElement = document.getElementById('game-status');

// Set canvas size
canvas.width = GAME_WIDTH;
canvas.height = GAME_HEIGHT;

// Adjust canvas size for Discord iframe if needed
function adjustCanvasForDiscord() {
    // Check if we're in Discord iframe
    const isInIframe = window !== window.parent;

    if (isInIframe) {
        // Get available width and height
        const availableWidth = window.innerWidth;
        const availableHeight = window.innerHeight;

        console.log(`Available space in iframe: ${availableWidth}x${availableHeight}`);

        // If available space is smaller than canvas, scale it down
        if (availableWidth < GAME_WIDTH || availableHeight < GAME_HEIGHT) {
            const scaleX = availableWidth / GAME_WIDTH * 0.9;
            const scaleY = availableHeight / GAME_HEIGHT * 0.7;
            const scale = Math.min(scaleX, scaleY);

            // Apply scale transform
            canvas.style.transform = `scale(${scale})`;
            canvas.style.transformOrigin = 'center top';

            console.log(`Scaling canvas by factor: ${scale}`);
        }
    }
}

// Call the adjustment function
adjustCanvasForDiscord();

// Re-adjust on window resize
window.addEventListener('resize', adjustCanvasForDiscord);

// Game state
let game = null;
let ai = null;
let gameLoop = null;
let clientId = ''; // Replace with your Discord client ID

// Initialize the game
async function initGame(mode = 'singleplayer', difficulty = 'medium', isActivity = false) {
    console.log(`Initializing game: mode=${mode}, difficulty=${difficulty}, isActivity=${isActivity}`);

    // Create a new game
    game = new SnakeGame(mode, difficulty);

    // Add the player
    game.addPlayer('player', GREEN);

    // Add AI opponent for singleplayer mode
    if (mode === 'singleplayer') {
        game.addPlayer('ai', BLUE);
        ai = new SnakeAI(game, difficulty);
    }

    // Initialize Discord SDK if we're in an activity
    if (isActivity) {
        console.log('Initializing as Discord Activity');
        const sdkInitialized = await initializeDiscordSDK(clientId);

        if (sdkInitialized) {
            // Set up Discord event listeners
            setupDiscordEventListeners(game);

            // Update Discord activity state
            updateActivityState(`Playing Snake (${mode})`);

            // Set up periodic state syncing for multiplayer
            if (mode === 'multiplayer') {
                console.log('Setting up multiplayer state syncing');
                // Sync game state every second
                setInterval(() => {
                    syncGameState(game);
                }, 1000);
            }
        }
    } else {
        console.log('Initializing as standalone game');
    }

    // Start the game loop
    startGameLoop();
}

// Start the game loop
function startGameLoop() {
    // Clear any existing game loop
    if (gameLoop) {
        clearInterval(gameLoop);
    }

    // Start a new game loop
    gameLoop = setInterval(() => {
        // Update AI if in singleplayer mode
        if (ai && game.snakes['ai'] && game.snakes['ai'].alive) {
            const aiDirection = ai.getNextMove();
            if (aiDirection) {
                game.handleInput('ai', aiDirection);
            }
        }

        // Update game state
        game.update();

        // Render the game
        renderGame();

        // Update scores in UI
        updateScores();

        // Check if game is over
        if (game.gameOver) {
            clearInterval(gameLoop);
            gameLoop = null;

            // Update game status
            if (game.winner) {
                const winnerName = game.winner === 'player' ? 'You' :
                                  (game.winner === 'ai' ? 'AI' : 'Player ' + game.winner);
                gameStatusElement.textContent = `Game Over! Winner: ${winnerName}`;
            } else {
                gameStatusElement.textContent = 'Game Over! It\'s a draw!';
            }

            // Update Discord activity state
            if (window.discordContext && window.discordContext.isActivity) {
                updateActivityState('Game Over');
            }

            // Show restart button or instructions
            showRestartInstructions();
        }
    }, 1000 / FPS);
}

// Update scores in the UI
function updateScores() {
    if (!game) return;

    // Update player score
    if (game.snakes['player']) {
        playerScoreElement.textContent = `${game.mode === 'multiplayer' ? 'Your' : 'Player'} Score: ${game.snakes['player'].score}`;
    }

    // Update AI score in singleplayer mode
    if (game.mode === 'singleplayer' && game.snakes['ai']) {
        aiScoreElement.textContent = `AI Score: ${game.snakes['ai'].score}`;
    }

    // In multiplayer mode, update other player scores
    if (game.mode === 'multiplayer') {
        // This would be expanded in a full implementation to show all player scores
        const otherPlayers = Object.keys(game.snakes).filter(id => id !== 'player');
        if (otherPlayers.length > 0) {
            aiScoreElement.textContent = `Other Players: ${otherPlayers.length}`;
        }
    }
}

// Show restart instructions
function showRestartInstructions() {
    const gameStatusElement = document.getElementById('game-status');
    if (!gameStatusElement) return;

    if (window.discordContext && window.discordContext.isActivity) {
        gameStatusElement.innerHTML += '<br>Type "/restart" to play again!';
    } else {
        gameStatusElement.innerHTML += '<br>Press R to restart';
    }
}

// Render the game
function renderGame() {
    // Clear the canvas
    ctx.fillStyle = BLACK;
    ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

    // Draw grid lines
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 1;

    // Draw vertical lines
    for (let x = 0; x <= GAME_WIDTH; x += CELL_SIZE) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, GAME_HEIGHT);
        ctx.stroke();
    }

    // Draw horizontal lines
    for (let y = 0; y <= GAME_HEIGHT; y += CELL_SIZE) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(GAME_WIDTH, y);
        ctx.stroke();
    }

    // Get the game state
    const state = game.getState();

    // Draw food
    state.food.forEach(food => {
        const x = food.x * CELL_SIZE;
        const y = food.y * CELL_SIZE;

        // Draw a red apple-like shape
        ctx.fillStyle = RED;
        ctx.beginPath();
        ctx.arc(
            x + CELL_SIZE / 2,
            y + CELL_SIZE / 2,
            CELL_SIZE / 2 - 2,
            0,
            Math.PI * 2
        );
        ctx.fill();
    });

    // Draw snakes
    Object.entries(state.snakes).forEach(([id, snake]) => {
        if (!snake.alive) return;

        // Draw each segment of the snake
        snake.body.forEach((segment, index) => {
            const x = segment.x * CELL_SIZE;
            const y = segment.y * CELL_SIZE;

            if (index === 0) {
                // Head
                ctx.fillStyle = snake.color;
                ctx.fillRect(
                    x + 1,
                    y + 1,
                    CELL_SIZE - 2,
                    CELL_SIZE - 2
                );

                // Eyes
                ctx.fillStyle = WHITE;
                const eyeSize = Math.max(2, CELL_SIZE / 5);
                ctx.beginPath();
                ctx.arc(
                    x + CELL_SIZE / 3,
                    y + CELL_SIZE / 3,
                    eyeSize / 2,
                    0,
                    Math.PI * 2
                );
                ctx.fill();

                ctx.beginPath();
                ctx.arc(
                    x + 2 * CELL_SIZE / 3,
                    y + CELL_SIZE / 3,
                    eyeSize / 2,
                    0,
                    Math.PI * 2
                );
                ctx.fill();
            } else {
                // Body
                ctx.fillStyle = snake.color;
                ctx.fillRect(
                    x + 2,
                    y + 2,
                    CELL_SIZE - 4,
                    CELL_SIZE - 4
                );
            }
        });

        // We'll handle score updates in the updateScores function
    });

    // Draw game over message if applicable
    if (state.gameOver) {
        // Semi-transparent overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

        // Game over text
        ctx.fillStyle = WHITE;
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', GAME_WIDTH / 2, GAME_HEIGHT / 3);

        // Winner text
        if (state.winner) {
            const winnerColor = state.snakes[state.winner]?.color || WHITE;
            ctx.fillStyle = winnerColor;
            ctx.font = '18px Arial';
            ctx.fillText(
                `Winner: ${state.winner}`,
                GAME_WIDTH / 2,
                GAME_HEIGHT / 2
            );
        } else {
            ctx.fillStyle = WHITE;
            ctx.font = '18px Arial';
            ctx.fillText(
                'It\'s a draw!',
                GAME_WIDTH / 2,
                GAME_HEIGHT / 2
            );
        }
    }
}

// Set up control buttons
document.getElementById('up-btn').addEventListener('click', () => {
    if (game) game.handleInput('player', Direction.UP);
});

document.getElementById('down-btn').addEventListener('click', () => {
    if (game) game.handleInput('player', Direction.DOWN);
});

document.getElementById('left-btn').addEventListener('click', () => {
    if (game) game.handleInput('player', Direction.LEFT);
});

document.getElementById('right-btn').addEventListener('click', () => {
    if (game) game.handleInput('player', Direction.RIGHT);
});

// Set up keyboard controls
document.addEventListener('keydown', (event) => {
    if (!game) return;

    switch (event.key) {
        case 'ArrowUp':
            game.handleInput('player', Direction.UP);
            break;
        case 'ArrowDown':
            game.handleInput('player', Direction.DOWN);
            break;
        case 'ArrowLeft':
            game.handleInput('player', Direction.LEFT);
            break;
        case 'ArrowRight':
            game.handleInput('player', Direction.RIGHT);
            break;
        case 'r':
        case 'R':
            // Restart the game if it's over
            if (game.gameOver) {
                restartGame();
            }
            break;
    }
});

// Restart the game
function restartGame() {
    if (!game) return;

    // Reset the game
    game.reset();

    // Add players based on mode
    game.addPlayer('player', GREEN);

    if (game.mode === 'singleplayer') {
        game.addPlayer('ai', BLUE);
        ai = new SnakeAI(game, game.aiDifficulty);
    }

    // Clear game status
    const gameStatusElement = document.getElementById('game-status');
    if (gameStatusElement) {
        gameStatusElement.textContent = '';
    }

    // Update Discord activity state
    if (window.discordContext && window.discordContext.isActivity) {
        updateActivityState(`Playing Snake (${game.mode})`);
    }

    // Start the game loop
    startGameLoop();
}

// Initialize the game when the page loads
window.addEventListener('load', () => {
    // Get game parameters from URL if available
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode') || 'singleplayer';
    const difficulty = urlParams.get('difficulty') || 'medium';
    const isActivity = urlParams.get('is_activity') === 'true';

    // Get Discord-specific parameters
    const guildId = urlParams.get('guild_id');
    const channelId = urlParams.get('channel_id');
    const activityId = urlParams.get('activity_id');

    // Store Discord context in window object for later use
    window.discordContext = {
        guildId,
        channelId,
        activityId,
        isActivity
    };

    console.log('Discord context:', window.discordContext);

    // Get client ID from URL or use a default
    clientId = urlParams.get('client_id') || '1375570370916253766';

    // Check if we're in an iframe (likely a Discord activity)
    const isInIframe = window !== window.parent;
    console.log('Running in iframe:', isInIframe);

    // If we're in an iframe and not explicitly marked as an activity, assume we are one
    if (isInIframe && !isActivity) {
        window.discordContext.isActivity = true;
        console.log('Auto-detected as Discord activity');

        // Add Discord iframe class to body for specific styling
        document.body.classList.add('discord-iframe');
    }

    // Apply Discord iframe class if explicitly marked as an activity
    if (isActivity) {
        document.body.classList.add('discord-iframe');
    }

    // Check with the server if we're running in Discord
    fetch(`/api/check-discord?is_iframe=${isInIframe}`)
        .then(response => response.json())
        .then(data => {
            console.log('Discord check:', data);

            // If we're in Discord, apply the Discord iframe class
            if (data.isDiscord) {
                document.body.classList.add('discord-iframe');
                console.log('Confirmed running in Discord');
            }

            // Apply additional styling adjustments for Discord iframe
            if (isInIframe || data.isDiscord || isActivity) {
                // Force the Discord iframe class
                document.body.classList.add('discord-iframe');

                // Apply additional styling
                const gameContainer = document.getElementById('game-container');
                if (gameContainer) {
                    gameContainer.style.padding = '5px';
                }

                // Adjust canvas size
                adjustCanvasForDiscord();
            }
        })
        .catch(error => {
            console.error('Failed to check Discord status:', error);

            // Apply Discord iframe class anyway if we're in an iframe
            if (isInIframe) {
                document.body.classList.add('discord-iframe');
            }
        });

    // Fetch configuration from the server
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            console.log('Server config:', config);

            // Update client ID if provided in config
            if (config.clientId) {
                clientId = config.clientId;
            }

            // Initialize the game with the activity flag
            initGame(mode, difficulty, window.discordContext.isActivity);

            // Update UI based on mode
            updateUIForMode(mode);
        })
        .catch(error => {
            console.error('Failed to fetch config:', error);

            // Initialize the game with default settings
            initGame(mode, difficulty, window.discordContext.isActivity);

            // Update UI based on mode
            updateUIForMode(mode);
        });
});

// Update UI elements based on game mode
function updateUIForMode(mode) {
    const aiScoreElement = document.getElementById('ai-score');

    if (mode === 'multiplayer') {
        // In multiplayer mode, hide the AI score
        if (aiScoreElement) {
            aiScoreElement.style.display = 'none';
        }

        // Update player score label
        const playerScoreElement = document.getElementById('player-score');
        if (playerScoreElement) {
            playerScoreElement.textContent = 'Your Score: 0';
        }

        // Add multiplayer instructions
        const gameStatusElement = document.getElementById('game-status');
        if (gameStatusElement) {
            gameStatusElement.textContent = 'Multiplayer mode: Invite friends to join!';
        }
    }
}
