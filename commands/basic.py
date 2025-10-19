"""
Basic bot commands: hello, ping
Simple commands for testing bot functionality
"""
import discord
from discord.commands import slash_command
from utils.logger import setup_logger

logger = setup_logger(__name__)


def setup(bot: discord.Bot):
    """Register basic commands with the bot"""
    
    @bot.slash_command(name="hello", description="บอทจะทักทายคุณกลับ")
    async def hello(ctx):
        """Greet the user"""
        logger.info(f"/hello command used by {ctx.author}")
        await ctx.respond(f"สวัสดีครับ, {ctx.author.name}!")
    
    @bot.slash_command(name="ping", description="ทดสอบความเร็วของบอท")
    async def ping(ctx):
        """Check bot latency"""
        latency_ms = round(bot.latency * 1000)
        logger.info(f"/ping command used by {ctx.author}, latency: {latency_ms}ms")
        await ctx.respond(f"Pong! 🏓 ความเร็ว: {latency_ms} ms")
    
    logger.info("Basic commands registered")
