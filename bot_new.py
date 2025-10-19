"""
Discord Stock Bot - Main Entry Point
Secure, optimized version for deployment on Render.com
"""
import discord
import os
from threading import Thread
from flask import Flask
from config import Config
from utils.logger import setup_logger
from commands import setup_all_commands

# Initialize logger
logger = setup_logger('StockBot')

# Simple web server for Render health checks
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Stock Bot is running! 🤖📈"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "online"}

def run_web_server():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    """Start web server in background thread"""
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    logger.info(f"Web server started on port {os.getenv('PORT', 10000)}")

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(str(e))
    exit(1)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True  # Required for some features
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f"✅ {bot.user} is online!")
    logger.info(f"Bot ID: {bot.user.id}")
    logger.info(f"Guilds: {len(bot.guilds)}")
    logger.info("=" * 50)


@bot.event
async def on_application_command_error(ctx, error):
    """Global error handler for slash commands"""
    logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)
    
    if isinstance(error, discord.errors.CheckFailure):
        await ctx.respond("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
    else:
        await ctx.respond(
            f"❌ เกิดข้อผิดพลาด: {str(error)}\n"
            "กรุณาลองใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบ",
            ephemeral=True
        )


# Register all commands
try:
    setup_all_commands(bot)
    logger.info("All commands registered successfully")
except Exception as e:
    logger.error(f"Failed to register commands: {e}", exc_info=True)
    exit(1)


# Run the bot
if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        
        # Start web server for Render health checks
        keep_alive()
        
        # Run Discord bot
        bot.run(Config.BOT_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("❌ Invalid Discord bot token!")
        exit(1)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)
