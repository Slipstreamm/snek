import discord
import asyncio
import os
import socket
import subprocess
import sys
from typing import Dict, Optional, Tuple
import config
from game.snake import Direction, SnakeGame
from game.renderer import GameRenderer

class EmbeddedAppManager:
    """Manages the embedded app for the Snake game."""

    def __init__(self):
        self.server_process = None
        self.server_port = 5010
        self.server_url = None

    async def start_server(self) -> bool:
        """Start the web server for the embedded app."""
        try:
            # Check if the server is already running
            if self.server_process and self.server_process.poll() is None:
                print("Server is already running")
                return True

            # Find an available port
            self.server_port = self._find_available_port()

            # Set the environment variables
            env = os.environ.copy()
            env['PORT'] = str(self.server_port)

            # Start the server process
            self.server_process = subprocess.Popen(
                [sys.executable, 'server.py'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait a bit for the server to start
            await asyncio.sleep(2)

            # Check if the server started successfully
            if self.server_process.poll() is not None:
                # Server failed to start
                stdout, stderr = self.server_process.communicate()
                print(f"Server failed to start: {stderr.decode('utf-8')}")
                return False

            # Set the server URL
            self.server_url = f"http://localhost:{self.server_port}"
            print(f"Server started at {self.server_url}")
            return True

        except Exception as e:
            print(f"Error starting server: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop_server(self):
        """Stop the web server."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("Server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print("Server killed")
            except Exception as e:
                print(f"Error stopping server: {e}")

            self.server_process = None

    def _find_available_port(self) -> int:
        """Find an available port to use for the server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

async def create_embedded_app(interaction: discord.Interaction, game: SnakeGame, renderer: GameRenderer) -> discord.Message:
    """Create and send the embedded app for a Snake game."""
    try:
        # Create an instance of the embedded app manager
        app_manager = EmbeddedAppManager()

        # Start the server
        server_started = await app_manager.start_server()
        if not server_started:
            raise Exception("Failed to start the embedded app server")

        # Create the initial game state image (for the thumbnail)
        game_state = game.get_state()
        img_str = renderer.render_game(game_state)

        # Convert base64 image to file
        import io
        import base64
        image_binary = base64.b64decode(img_str)
        file = discord.File(io.BytesIO(image_binary), filename="game_thumbnail.png")

        # Create the embed with the Activity
        embed = discord.Embed(
            title="Snake Game",
            description=f"Click below to play Snake in {game.mode.capitalize()} mode!",
            color=0x00ff00
        )

        # Add game info to the embed
        if game.mode == config.SINGLEPLAYER:
            embed.description += f" (AI: {game.ai_difficulty.capitalize()})"

        # Set the thumbnail
        embed.set_thumbnail(url=f"attachment://game_thumbnail.png")

        # Add instructions
        embed.add_field(
            name="How to Play",
            value="Use the arrow keys or on-screen buttons to control your snake. Collect food to grow and earn points!",
            inline=False
        )

        # Create the URL with game parameters
        app_url = f"{config.EMBEDDED_APP_URL}/discord-activity?mode={game.mode}&difficulty={game.ai_difficulty}"

        # Create the Activity component
        activity = discord.ui.View()
        activity.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Play Snake Game",
                url=app_url,
                emoji="🐍"
            )
        )

        # Try to send the message using followup first (which works in more contexts)
        try:
            # Check if we can use followup (if the interaction hasn't been responded to yet)
            if not interaction.response.is_done():
                await interaction.response.send_message("Preparing game...", ephemeral=True)

            # Use followup to send the game interface
            message = await interaction.followup.send(embed=embed, file=file, view=activity)
            return message
        except Exception as followup_error:
            print(f"Failed to send using followup: {followup_error}")

            # Fall back to channel.send if followup fails
            message = await interaction.channel.send(embed=embed, file=file, view=activity)
            return message

    except discord.errors.Forbidden as e:
        print(f"Permission error creating embedded app: {e}")

        # Try to send a simple error message
        try:
            error_message = "I don't have permission to send game messages in this channel. Please check my permissions."
            if not interaction.response.is_done():
                await interaction.response.send_message(error_message, ephemeral=True)
            else:
                await interaction.followup.send(error_message, ephemeral=True)
        except Exception:
            pass  # If this fails too, we've done all we can

        # Re-raise as a more specific error
        raise discord.errors.Forbidden(e.response, e.text) from e

    except Exception as e:
        print(f"Error creating embedded app: {e}")
        import traceback
        traceback.print_exc()

        # Try to send a simple error message
        try:
            error_message = "Failed to create the game interface. Please try again or contact the bot administrator."
            if not interaction.response.is_done():
                await interaction.response.send_message(error_message, ephemeral=True)
            else:
                await interaction.followup.send(error_message, ephemeral=True)
        except Exception as msg_error:
            print(f"Failed to send error message: {msg_error}")

        # Re-raise the exception to be handled by the caller
        raise Exception(f"Failed to create embedded app: {str(e)}") from e
