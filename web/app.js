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

// Game state
let game = null;
let ai = null;
let gameLoop = null;
let clientId = ''; // Replace with your Discord client ID

// Initialize the game
async function initGame(mode = 'singleplayer', difficulty = 'medium') {
    // Create a new game
    game = new SnakeGame(mode, difficulty);

    // Add the player
    game.addPlayer('player', GREEN);

    // Add AI opponent for singleplayer mode
    if (mode === 'singleplayer') {
        game.addPlayer('ai', BLUE);
        ai = new SnakeAI(game, difficulty);
    }

    // Initialize Discord SDK
    const sdkInitialized = await initializeDiscordSDK(clientId);

    if (sdkInitialized) {
        // Set up Discord event listeners
        setupDiscordEventListeners(game);

        // Update Discord activity state
        updateActivityState(`Playing Snake (${mode})`);
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

        // Check if game is over
        if (game.gameOver) {
            clearInterval(gameLoop);
            gameLoop = null;

            // Update game status
            if (game.winner) {
                gameStatusElement.textContent = `Game Over! Winner: ${game.winner}`;
            } else {
                gameStatusElement.textContent = 'Game Over! It\'s a draw!';
            }

            // Update Discord activity state
            updateActivityState('Game Over');
        }
    }, 1000 / FPS);
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

        // Update score display
        if (id === 'player') {
            playerScoreElement.textContent = `Player: ${snake.score}`;
        } else if (id === 'ai') {
            aiScoreElement.textContent = `AI: ${snake.score}`;
        }
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
    }
});

// Initialize the game when the page loads
window.addEventListener('load', () => {
    // Get game parameters from URL if available
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode') || 'singleplayer';
    const difficulty = urlParams.get('difficulty') || 'medium';
    const isActivity = urlParams.get('is_activity') === 'true';

    // Get client ID from URL or use a default
    clientId = urlParams.get('client_id') || '1375570370916253766';

    // Fetch configuration from the server
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            console.log('Server config:', config);

            // Update client ID if provided in config
            if (config.clientId) {
                clientId = config.clientId;
            }

            // Initialize the game
            initGame(mode, difficulty);
        })
        .catch(error => {
            console.error('Failed to fetch config:', error);

            // Initialize the game with default settings
            initGame(mode, difficulty);
        });
});
