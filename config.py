"""
Configuration file for the Discord Stock Bot
Handles environment variables and application settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Discord Bot Token (REQUIRED)
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Rate Limiting
    MAX_NEWS_ITEMS = 10
    MAX_MARKET_DATA_STOCKS = 503  # S&P 500
    
    # Cache settings (for future optimization)
    CACHE_ENABLED = True
    CACHE_TTL = 300  # 5 minutes
    
    # Translation settings
    TRANSLATION_MAX_LENGTH = 5000
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            raise ValueError(
                "DISCORD_BOT_TOKEN is not set. "
                "Please create a .env file with your bot token. "
                "See .env.example for reference."
            )
        return True
