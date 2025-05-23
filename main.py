import asyncio
import discord
import config
from discord_integration.bot import SnakeBot

async def main():
    """Main entry point for the Discord bot."""
    # Check if token is available
    if not config.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        print("Please create a .env file with your Discord bot token.")
        return

    # Create and start the bot
    bot = SnakeBot()

    try:
        print("Starting bot...")
        await bot.start(config.DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord token. Please check your .env file.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())