"""
Translation utilities using Google Translate
Handles English to Thai translation for news content
"""
from deep_translator import GoogleTranslator
from config import Config
from .logger import setup_logger

logger = setup_logger(__name__)


def translate_to_thai(text: str) -> str:
    """
    Translate text from English to Thai
    
    Args:
        text: English text to translate
        
    Returns:
        Translated Thai text, or original text if translation fails
    """
    if not text or not text.strip():
        return text
    
    try:
        translator = GoogleTranslator(source='en', target='th')
        
        # Truncate if too long
        if len(text) > Config.TRANSLATION_MAX_LENGTH:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {Config.TRANSLATION_MAX_LENGTH}")
            text = text[:Config.TRANSLATION_MAX_LENGTH]
        
        translated = translator.translate(text)
        logger.debug(f"Translated: {text[:50]}... -> {translated[:50]}...")
        return translated
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text  # Return original text if translation fails
