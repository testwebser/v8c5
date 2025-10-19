"""
Stock information command
Display current stock price and basic information
"""
import discord
from discord.commands import slash_command, Option
import yfinance as yf
from utils.logger import setup_logger

logger = setup_logger(__name__)


def setup(bot: discord.Bot):
    """Register stock command with the bot"""
    
    @bot.slash_command(name="stock", description="ดูข้อมูลหุ้นรายตัว")
    async def stock(
        ctx,
        symbol: Option(str, "สัญลักษณ์หุ้น (เช่น AAPL, HIVE, NVDA)", required=True)
    ):
        """
        Get stock information
        
        Args:
            symbol: Stock ticker symbol
        """
        logger.info(f"/stock {symbol} command used by {ctx.author}")
        await ctx.defer()
        
        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            
            if 'shortName' not in info or info['shortName'] is None:
                logger.warning(f"Stock symbol not found: {symbol}")
                await ctx.respond(f"❌ ไม่พบข้อมูลสำหรับสัญลักษณ์ '{symbol}' ครับ")
                return

            embed = discord.Embed(
                title=f"ข้อมูลหุ้น {info.get('shortName', symbol.upper())} ({symbol.upper()})",
                color=discord.Color.blue()
            )

            current_price = info.get('currentPrice', 'N/A')
            previous_close = info.get('previousClose', 'N/A')
            change_str = "N/A"
            
            if isinstance(current_price, (int, float)) and isinstance(previous_close, (int, float)):
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                sign = "+" if change >= 0 else ""
                change_str = f"{sign}{change:.2f} ({sign}{change_percent:.2f}%)"
                embed.color = discord.Color.green() if change >= 0 else discord.Color.red()

            embed.add_field(name="ราคาปัจจุบัน", value=f"**${current_price}**", inline=True)
            embed.add_field(name="การเปลี่ยนแปลง", value=f"**{change_str}**", inline=True)
            embed.add_field(name="ราคาปิดวันก่อน", value=f"${info.get('previousClose', 'N/A')}", inline=False)
            embed.add_field(name="ราคาเปิด", value=f"${info.get('open', 'N/A')}", inline=True)
            embed.add_field(name="ช่วงราคาวันนี้", value=f"${info.get('dayLow', 'N/A')} - ${info.get('dayHigh', 'N/A')}", inline=True)
            embed.add_field(name="ปริมาณการซื้อขาย", value=f"{info.get('volume', 0):,}", inline=False)
            embed.add_field(name="Market Cap", value=f"{info.get('marketCap', 0):,}", inline=True)
            embed.add_field(name="P/E (TTM)", value=f"{info.get('trailingPE', 'N/A')}", inline=True)

            await ctx.respond(embed=embed)
            logger.info(f"Stock info sent for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in /stock {symbol}: {e}", exc_info=True)
            await ctx.respond(f"เกิดข้อผิดพลาดขณะดึงข้อมูล {symbol} ครับ")
    
    logger.info("Stock command registered")
