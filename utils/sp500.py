"""
S&P 500 data fetching utilities
Retrieves the list of S&P 500 companies from Wikipedia
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from .logger import setup_logger

logger = setup_logger(__name__)


def get_sp500_symbols() -> Optional[List[str]]:
    """
    Fetch S&P 500 stock symbols from Wikipedia
    
    Returns:
        List of stock symbols, or None if fetching fails
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        logger.info("Fetching S&P 500 symbols from Wikipedia...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'})
        
        if not table:
            logger.error("Could not find constituents table on Wikipedia")
            return None
        
        symbols = []
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if cells:
                symbol = cells[0].text.strip()
                # yfinance uses - instead of . in some tickers
                symbol = symbol.replace('.', '-')
                symbols.append(symbol)
        
        logger.info(f"Successfully fetched {len(symbols)} S&P 500 symbols")
        return symbols
        
    except requests.RequestException as e:
        logger.error(f"HTTP error while fetching S&P 500 symbols: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching S&P 500 symbols: {e}")
        return None
