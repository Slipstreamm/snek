// Discord SDK Integration
let discordSdk = null;
let currentUser = null;
let auth = null;

// Initialize the Discord SDK
async function initializeDiscordSDK(clientId) {
    try {
        // Check if the SDK is loaded
        if (typeof DiscordSDK === 'undefined') {
            console.error('Discord SDK not loaded');
            return false;
        }

        // Create a new instance of the Discord SDK
        discordSdk = new DiscordSDK(clientId);

        // Wait for the SDK to be ready
        await discordSdk.ready();
        console.log('Discord SDK ready');

        // Check if we're running in an Activity context
        const activityContext = await discordSdk.commands.getContext();
        console.log('Activity context:', activityContext);

        if (activityContext && activityContext.activity) {
            console.log('Running as a Discord Activity');

            // Authorize with Discord
            try {
                const { code } = await discordSdk.commands.authorize({
                    client_id: clientId,
                    response_type: 'code',
                    state: '',
                    prompt: 'none',
                    scope: ['identify', 'activities.write', 'activities.read'],
                });

                console.log('Authorization successful');

                // Authenticate with Discord
                auth = await discordSdk.commands.authenticate({
                    access_token: code, // In a real app, you'd exchange this code for a token
                });

                console.log('Authentication successful');

                // Set up activity-specific features
                await setupActivityFeatures();
            } catch (authError) {
                console.error('Authorization/Authentication error:', authError);
                // Continue without authentication
            }
        } else {
            console.log('Not running as a Discord Activity, using standalone mode');
        }

        // Try to get the current user
        try {
            currentUser = await discordSdk.commands.user.getUser();
            console.log('User identified as:', currentUser.username);
        } catch (userError) {
            console.error('Failed to get user:', userError);
        }

        return true;
    } catch (error) {
        console.error('Failed to initialize Discord SDK:', error);
        return false;
    }
}

// Set up Activity-specific features
async function setupActivityFeatures() {
    try {
        // Register for activity launch
        await discordSdk.commands.activity.onActivityStart((data) => {
            console.log('Activity started with data:', data);

            // Initialize the game with specific settings from the activity launch
            if (data && data.params) {
                const mode = data.params.mode || 'singleplayer';
                const difficulty = data.params.difficulty || 'medium';

                console.log(`Starting game with mode: ${mode}, difficulty: ${difficulty}`);

                // If we already have a game instance, reset it with new parameters
                if (window.game) {
                    window.game.reset();

                    // Re-add players based on mode
                    window.game.mode = mode;
                    window.game.aiDifficulty = difficulty;
                    window.game.addPlayer('player', GREEN);

                    if (mode === 'singleplayer') {
                        window.game.addPlayer('ai', BLUE);
                        window.ai = new SnakeAI(window.game, difficulty);
                    }
                }
            }
        });

        // Set up voice channel integration for multiplayer coordination
        await discordSdk.commands.activity.registerVoiceChannelCallback((voiceState) => {
            console.log('Voice channel state updated:', voiceState);

            // You can use this to coordinate multiplayer sessions
            if (voiceState.joined) {
                console.log(`User ${voiceState.user.username} joined the voice channel`);

                // If in multiplayer mode, we could add them as a player
                if (window.game && window.game.mode === 'multiplayer') {
                    const userId = voiceState.user.id;
                    if (!window.game.snakes[userId]) {
                        window.game.addPlayer(userId, YELLOW);
                        sendDiscordMessage(`${voiceState.user.username} has joined the game!`);
                    }
                }
            } else if (voiceState.left) {
                console.log(`User ${voiceState.user.username} left the voice channel`);
            }
        });

        // Set up activity participants tracking
        await discordSdk.commands.activity.registerParticipantsChangeCallback((participants) => {
            console.log('Activity participants changed:', participants);

            // Update the UI to show who's in the activity
            updateParticipantsUI(participants);
        });

        console.log('Activity features set up successfully');
    } catch (error) {
        console.error('Failed to set up activity features:', error);
    }
}

// Update the UI to show participants
function updateParticipantsUI(participants) {
    // This function would update some UI element to show who's in the activity
    console.log(`${participants.length} participants in the activity`);
}

// Send a message to the Discord channel
async function sendDiscordMessage(message) {
    if (!discordSdk) return;

    try {
        await discordSdk.commands.message.send({
            content: message,
        });
    } catch (error) {
        console.error('Failed to send message:', error);
    }
}

// Update the activity state
async function updateActivityState(state, gameState = null) {
    if (!discordSdk) return;

    try {
        // Create the activity payload
        const activityPayload = {
            state: state,
            details: `Snake Game - ${window.game ? window.game.mode : 'Loading...'}`,
            timestamps: {
                start: Date.now()
            },
            assets: {
                large_image: 'snake_game', // This would be an asset ID from your Discord application
                large_text: 'Snake Game',
                small_image: 'discord_logo',
                small_text: 'Powered by Discord'
            },
            party: {
                id: `snake_${Date.now()}`,
                size: [
                    window.game ? Object.keys(window.game.snakes).length : 1,
                    window.game && window.game.mode === 'multiplayer' ? 8 : 2
                ]
            },
            secrets: {
                join: `snake_join_${Date.now()}`
            }
        };

        // If we have game state to sync, add it
        if (gameState) {
            activityPayload.state = {
                gameState: gameState
            };
        }

        // Set the activity
        await discordSdk.commands.setActivity(activityPayload);
        console.log('Activity state updated:', state);
    } catch (error) {
        console.error('Failed to update activity state:', error);
    }
}

// Sync game state with other players
async function syncGameState(game) {
    if (!discordSdk || !game) return;

    try {
        // Get the current game state
        const gameState = game.getState();

        // Update the activity with the game state
        await updateActivityState(`Playing Snake (${game.mode})`, gameState);
    } catch (error) {
        console.error('Failed to sync game state:', error);
    }
}

// Set up event listeners for Discord SDK events
function setupDiscordEventListeners(game) {
    if (!discordSdk) return;

    // Store the game instance in the window object for global access
    window.game = game;

    // Set up command handling for the activity
    discordSdk.commands.activity.registerCommand({
        name: 'move',
        description: 'Move your snake in a direction',
        options: [
            {
                name: 'direction',
                description: 'Direction to move',
                type: 3, // STRING type
                required: true,
                choices: [
                    { name: 'Up', value: 'up' },
                    { name: 'Down', value: 'down' },
                    { name: 'Left', value: 'left' },
                    { name: 'Right', value: 'right' }
                ]
            }
        ],
        execute: async (interaction) => {
            const direction = interaction.options.getString('direction');
            const userId = interaction.user.id;

            // If this user doesn't have a snake and we're in multiplayer mode, add them
            if (game.mode === 'multiplayer' && !game.snakes[userId]) {
                game.addPlayer(userId, YELLOW);
                await interaction.reply(`You've joined the game!`);
            }

            // Handle the movement
            switch (direction) {
                case 'up':
                    game.handleInput(userId, Direction.UP);
                    break;
                case 'down':
                    game.handleInput(userId, Direction.DOWN);
                    break;
                case 'left':
                    game.handleInput(userId, Direction.LEFT);
                    break;
                case 'right':
                    game.handleInput(userId, Direction.RIGHT);
                    break;
            }

            await interaction.reply(`Moved ${direction}!`);
        }
    });

    // Register restart command
    discordSdk.commands.activity.registerCommand({
        name: 'restart',
        description: 'Restart the game',
        execute: async (interaction) => {
            // Only allow restarting if the game is over
            if (game.gameOver) {
                game.reset();
                game.addPlayer('player', GREEN);
                if (game.mode === 'singleplayer') {
                    game.addPlayer('ai', BLUE);
                }
                await interaction.reply('Game restarted!');
            } else {
                await interaction.reply('Cannot restart while game is in progress!');
            }
        }
    });

    // Listen for activity state updates
    discordSdk.on('ACTIVITY_STATE_UPDATE', (state) => {
        console.log('Activity state updated:', state);

        // You can use this to sync game state between players
        if (state.state && state.state.gameState) {
            // This would be used in a more complex implementation to sync game state
            console.log('Received game state update:', state.state.gameState);
        }
    });

    // Listen for user join/leave events
    discordSdk.on('VOICE_STATE_UPDATE', (state) => {
        if (state.user && state.channel_id) {
            console.log(`User ${state.user.username} joined voice channel`);
        } else if (state.user) {
            console.log(`User ${state.user.username} left voice channel`);
        }
    });
}
