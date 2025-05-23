import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import config
from typing import Dict, Optional
from game.snake import SnakeGame, Direction
from game.ai import SnakeAI
from game.renderer import GameRenderer
from discord_integration.embedded_app import create_embedded_app

class SnakeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

        # Store active games
        self.active_games: Dict[int, Dict] = {}  # channel_id -> game_data
        self.game_renderer = GameRenderer()

        # Register commands
        self.setup_commands()

    async def on_ready(self):
        """Called when the bot is ready."""
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

        # Sync commands with Discord
        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'Failed to sync commands: {e}')

    def setup_commands(self):
        """Set up the bot commands."""
        @app_commands.allowed_installs(guilds=True, users=True)
        @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
        @self.tree.command(name="snek", description="Start a new Snake game")
        @app_commands.describe(
            mode="Game mode (singleplayer or multiplayer)",
            difficulty="AI difficulty for singleplayer mode (easy, medium, hard)"
        )
        @app_commands.choices(
            mode=[
                app_commands.Choice(name="Singleplayer", value="singleplayer"),
                app_commands.Choice(name="Multiplayer", value="multiplayer")
            ],
            difficulty=[
                app_commands.Choice(name="Easy", value="easy"),
                app_commands.Choice(name="Medium", value="medium"),
                app_commands.Choice(name="Hard", value="hard")
            ]
        )
        async def snek_command(
            interaction: discord.Interaction,
            mode: str = "singleplayer",
            difficulty: str = "medium"
        ):
            """Start a new Snake game."""
            await self.start_game(interaction, mode, difficulty)

        @self.tree.command(name="snek_help", description="Show help for the Snake game")
        @app_commands.allowed_installs(guilds=True, users=True)
        @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
        async def snek_help_command(interaction: discord.Interaction):
            """Show help for the Snake game."""
            await self.show_help(interaction)

    async def start_game(self, interaction: discord.Interaction, mode: str, difficulty: str):
        """Start a new Snake game."""
        channel_id = interaction.channel_id

        # Check if there's already an active game in this channel
        if channel_id in self.active_games:
            await interaction.response.send_message(
                "There's already an active game in this channel. "
                "Please wait for it to finish or use the embedded app controls.",
                ephemeral=True
            )
            return

        # Check permissions if in a guild (server) channel
        # DMs and group DMs have different permission handling
        if interaction.guild:
            channel = interaction.channel
            permissions = channel.permissions_for(interaction.guild.me)

            # Check if the bot has permission to send messages in this channel
            if not permissions.send_messages:
                await interaction.response.send_message(
                    "I don't have permission to send messages in this channel. "
                    "Please ask a server admin to grant me the 'Send Messages' permission.",
                    ephemeral=True
                )
                return

            # Check if the bot has permission to embed links and attach files
            if not permissions.embed_links or not permissions.attach_files:
                await interaction.response.send_message(
                    "I don't have permission to send embeds or attachments in this channel. "
                    "Please ask a server admin to grant me the 'Embed Links' and 'Attach Files' permissions.",
                    ephemeral=True
                )
                return

        # Respond to the interaction immediately to prevent timeout
        await interaction.response.defer(ephemeral=False, thinking=True)

        try:
            # Create a new game
            game = SnakeGame(mode, difficulty)

            # Add the player
            player_id = str(interaction.user.id)
            player_name = interaction.user.display_name
            game.add_player('player', config.GREEN)

            # Add AI opponent for singleplayer mode
            if mode == config.SINGLEPLAYER:
                game.add_player('ai', config.BLUE)
                ai = SnakeAI(game, difficulty)
            else:
                ai = None

            try:
                # Create the embedded app
                app_message = await create_embedded_app(interaction, game, self.game_renderer)

                # Store the game data
                self.active_games[channel_id] = {
                    'game': game,
                    'ai': ai,
                    'message': app_message,
                    'task': None,
                    'players': {player_id: player_name}
                }

                # Start the game loop
                game_task = asyncio.create_task(self.game_loop(channel_id))
                self.active_games[channel_id]['task'] = game_task

                # Send a follow-up message instead of responding to the interaction
                await interaction.followup.send(
                    f"Snake game started in {mode} mode! "
                    f"Use the embedded app to play."
                )
            except discord.errors.Forbidden as e:
                await interaction.followup.send(
                    "I don't have permission to send game messages in this channel. "
                    "Please ask a server admin to check my permissions.",
                    ephemeral=True
                )
                print(f"Permission error: {e}")

        except Exception as e:
            print(f"Error starting game: {e}")
            import traceback
            traceback.print_exc()

            try:
                await interaction.followup.send(
                    f"An error occurred while starting the game: {str(e)}",
                    ephemeral=True
                )
            except Exception as follow_error:
                print(f"Failed to send error message: {follow_error}")

    async def game_loop(self, channel_id: int):
        """Main game loop for a Snake game."""
        if channel_id not in self.active_games:
            print(f"Game loop started for non-existent game in channel {channel_id}")
            return

        game_data = self.active_games[channel_id]
        game = game_data['game']
        ai = game_data['ai']
        message = game_data['message']  # Keep this for reference even if not directly used

        try:
            while not game.game_over and channel_id in self.active_games:
                # Update AI if in singleplayer mode
                if ai and 'ai' in game.snakes and game.snakes['ai'].alive:
                    ai_direction = ai.get_next_move()
                    game.handle_input('ai', ai_direction)

                # Update game state
                game.update()

                # Update the embedded app
                try:
                    await self.update_embedded_app(channel_id)
                except discord.errors.Forbidden:
                    print(f"Permission error updating game in channel {channel_id}")
                    # End the game if we can't update it
                    game.game_over = True
                except discord.errors.NotFound:
                    print(f"Channel or message not found for game in channel {channel_id}")
                    # End the game if the channel or message is gone
                    game.game_over = True
                except Exception as update_error:
                    print(f"Error updating game: {update_error}")
                    # Continue the game even if we can't update it

                # Sleep to control game speed
                await asyncio.sleep(1.0 / config.FPS)

            # Game is over, update one last time
            try:
                await self.update_embedded_app(channel_id)
            except Exception as final_update_error:
                print(f"Error in final game update: {final_update_error}")

            # Wait a bit before cleaning up
            await asyncio.sleep(5)

            # Clean up
            if channel_id in self.active_games:
                del self.active_games[channel_id]
                print(f"Game in channel {channel_id} ended and cleaned up")

        except Exception as e:
            print(f"Error in game loop: {e}")
            import traceback
            traceback.print_exc()

            # Try to send an error message to the channel
            try:
                channel = self.get_channel(channel_id)
                if channel:
                    await channel.send(f"An error occurred in the Snake game: {str(e)}")
            except Exception as msg_error:
                print(f"Failed to send error message: {msg_error}")

            # Clean up on error
            if channel_id in self.active_games:
                del self.active_games[channel_id]
                print(f"Game in channel {channel_id} ended due to error and cleaned up")

    async def update_embedded_app(self, channel_id: int):
        """Update the embedded app for a game."""
        if channel_id not in self.active_games:
            return

        game_data = self.active_games[channel_id]
        game = game_data['game']
        message = game_data['message']

        try:
            # Get the game state
            game_state = game.get_state()

            # Render the game state to an image for the thumbnail
            img_str = self.game_renderer.render_game(game_state)

            # Create an embed with the game status
            embed = discord.Embed(title="Snake Game", color=0x00ff00)

            # Add game info to the embed
            if game.game_over:
                if game.winner:
                    embed.description = f"Game Over! Winner: {game.winner}"
                else:
                    embed.description = "Game Over! It's a draw!"

                # Add a "Play Again" button
                embed.add_field(
                    name="Play Again",
                    value="Use the `/snek` command to start a new game!",
                    inline=False
                )
            else:
                embed.description = f"Snake game is running in {game.mode.capitalize()} mode"
                if game.mode == config.SINGLEPLAYER:
                    embed.description += f" (AI: {game.ai_difficulty.capitalize()})"

                embed.add_field(
                    name="Status",
                    value="Game is in progress. Click the button below to play!",
                    inline=False
                )

            # Add player scores
            for player_id, snake_data in game_state['snakes'].items():
                player_name = player_id
                if player_id in game_data['players']:
                    player_name = game_data['players'][player_id]
                embed.add_field(
                    name=f"{player_name}",
                    value=f"Score: {snake_data['score']}",
                    inline=True
                )

            # Convert base64 image to file for the thumbnail
            import io
            import base64
            image_binary = base64.b64decode(img_str)
            file = discord.File(io.BytesIO(image_binary), filename="game_thumbnail.png")

            # Set the thumbnail
            embed.set_thumbnail(url=f"attachment://game_thumbnail.png")

            # We don't need to update the view (button) since it's a link that doesn't change

            # Update the message
            await message.edit(embed=embed, attachments=[file])

        except discord.errors.NotFound:
            # Message was deleted or channel no longer exists
            print(f"Message or channel not found when updating game in channel {channel_id}")
            game.game_over = True  # End the game
            raise  # Re-raise to be handled by the caller

        except discord.errors.Forbidden as e:
            # Bot doesn't have permission to edit the message
            print(f"Permission error updating game in channel {channel_id}: {e}")
            game.game_over = True  # End the game
            raise  # Re-raise to be handled by the caller

        except Exception as e:
            print(f"Error updating embedded app: {e}")
            import traceback
            traceback.print_exc()

            # Try a simpler update without the image if possible
            try:
                simple_embed = discord.Embed(
                    title="Snake Game",
                    description="Game display error. The game is still running.",
                    color=0xFF0000
                )
                await message.edit(embed=simple_embed, attachments=[])
            except Exception:
                # If even this fails, re-raise the original exception
                raise

    async def show_help(self, interaction: discord.Interaction):
        """Show help for the Snake game."""
        embed = discord.Embed(
            title="Snake Game Help",
            description="Welcome to Snake! Here's how to play:",
            color=0x00ff00
        )

        embed.add_field(
            name="Starting a Game",
            value="Use `/snek` to start a new game. You can choose between singleplayer and multiplayer modes.",
            inline=False
        )

        embed.add_field(
            name="Game Modes",
            value=(
                "**Singleplayer**: Play against an AI opponent. You can choose the difficulty level.\n"
                "**Multiplayer**: Play against another Discord user."
            ),
            inline=False
        )

        embed.add_field(
            name="How to Play",
            value=(
                "1. Click the 'Play Snake Game' button to open the embedded app\n"
                "2. Use arrow keys or on-screen buttons to control your snake\n"
                "3. Collect food (red dots) to grow your snake and earn points\n"
                "4. Avoid colliding with walls, other snakes, or yourself!"
            ),
            inline=False
        )

        embed.add_field(
            name="Embedded App",
            value=(
                "The game now runs as a full embedded app in Discord!\n"
                "This provides a smoother experience with better controls and visuals.\n"
                "The game state is synchronized between all players in real-time."
            ),
            inline=False
        )

        embed.add_field(
            name="Commands",
            value=(
                "`/snek` - Start a new Snake game\n"
                "`/snek_help` - Show this help message"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
