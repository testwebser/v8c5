"""Discord bot commands organized by category"""

def setup_all_commands(bot):
    """Register all command modules with the bot"""
    from . import basic, stock, analysis, market, news
    
    basic.setup(bot)
    stock.setup(bot)
    analysis.setup(bot)
    market.setup(bot)
    news.setup(bot)
