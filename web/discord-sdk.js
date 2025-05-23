// Discord SDK Integration
let discordSdk = null;
let currentUser = null;

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

            // Set up activity-specific features
            await setupActivityFeatures();
        } else {
            console.log('Not running as a Discord Activity, using standalone mode');
        }

        // Try to authenticate the user
        try {
            // Get the current user
            currentUser = await discordSdk.commands.user.getUser();
            console.log('User identified as:', currentUser.username);

            return true;
        } catch (authError) {
            console.error('Authentication error:', authError);
            // Continue without authentication
            return true;
        }
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

            // You can use this to initialize the game with specific settings
            if (data && data.params) {
                // Example: data.params.mode, data.params.difficulty
                console.log('Activity params:', data.params);
            }
        });

        // Set up voice channel integration
        await discordSdk.commands.activity.registerVoiceChannelCallback((voiceState) => {
            console.log('Voice channel state updated:', voiceState);
        });

        console.log('Activity features set up successfully');
    } catch (error) {
        console.error('Failed to set up activity features:', error);
    }
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
async function updateActivityState(state) {
    if (!discordSdk) return;

    try {
        await discordSdk.commands.setActivity({
            state: state,
        });
    } catch (error) {
        console.error('Failed to update activity state:', error);
    }
}

// Set up event listeners for Discord SDK events
function setupDiscordEventListeners(game) {
    if (!discordSdk) return;

    // Listen for input events from other users
    discordSdk.on('MESSAGE_CREATE', async (message) => {
        // Check if the message is a game command
        if (message.content.startsWith('!snake ')) {
            const command = message.content.substring(7).trim();

            // Handle different commands
            switch (command) {
                case 'up':
                    game.handleInput('player', Direction.UP);
                    break;
                case 'down':
                    game.handleInput('player', Direction.DOWN);
                    break;
                case 'left':
                    game.handleInput('player', Direction.LEFT);
                    break;
                case 'right':
                    game.handleInput('player', Direction.RIGHT);
                    break;
                case 'join':
                    // Add a new player if in multiplayer mode
                    if (game.mode === 'multiplayer' && !game.snakes[message.author.id]) {
                        game.addPlayer(message.author.id, '#FFFF00'); // Yellow color
                        sendDiscordMessage(`${message.author.username} has joined the game!`);
                    }
                    break;
                case 'restart':
                    // Only allow restarting if the game is over
                    if (game.gameOver) {
                        game.reset();
                        game.addPlayer('player', '#00FF00'); // Green color
                        if (game.mode === 'singleplayer') {
                            game.addPlayer('ai', '#0000FF'); // Blue color
                        }
                        sendDiscordMessage('Game restarted!');
                    }
                    break;
            }
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
