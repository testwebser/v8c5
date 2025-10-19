"""
Market data command
Display S&P 500 market overview with top gainers, losers, and most active
"""
import discord
from discord.commands import slash_command, Option
import yfinance as yf
import pandas as pd
import datetime
import time
from utils.logger import setup_logger
from utils.sp500 import get_sp500_symbols

logger = setup_logger(__name__)


def setup(bot: discord.Bot):
    """Register market command with the bot"""
    
    @bot.slash_command(name="marketdata", description="สรุปภาพรวมตลาด (S&P 500)")
    async def marketdata(
        ctx,
        top_n: Option(int, "จำนวนหุ้นที่จะแสดง (Top N)", default=5, min_value=3, max_value=10)
    ):
        """Get S&P 500 market overview"""
        logger.info(f"/marketdata command used by {ctx.author}")
        await ctx.defer(ephemeral=False)
        
        try:
            await ctx.respond(f"กำลังดึงข้อมูลสรุปตลาด (S&P 500)... นี่อาจใช้เวลา 1-2 นาทีนะครับ ☕")

            # Get S&P 500 symbols
            symbols = get_sp500_symbols()
            if not symbols:
                await ctx.edit(content="❌ เกิดข้อผิดพลาดในการดึงรายชื่อหุ้น S&P 500 ครับ")
                return

            # Fetch stock data
            end_date = datetime.date.today()
            start_date = end_date - pd.DateOffset(days=5)
            
            # Download in chunks to avoid rate limiting
            all_close_data = []
            all_volume_data = []
            symbols_chunks = [symbols[i:i + 100] for i in range(0, len(symbols), 100)]
            
            for i, chunk in enumerate(symbols_chunks):
                logger.info(f"Fetching S&P 500 data chunk {i+1}/{len(symbols_chunks)}...")
                data = yf.download(chunk, start=start_date, end=end_date, progress=False, auto_adjust=True)
                
                if not data.empty:
                    if 'Close' in data.columns:
                        all_close_data.append(data['Close'])
                    if 'Volume' in data.columns:
                        all_volume_data.append(data['Volume'])
                
                time.sleep(1)  # Rate limiting
            
            if not all_close_data:
                await ctx.edit(content="❌ ไม่สามารถดึงข้อมูลราคาปิดได้ครับ")
                return
                
            all_close = pd.concat(all_close_data, axis=1)
            all_volume = pd.concat(all_volume_data, axis=1)

            # Process data
            if all_close.empty:
                await ctx.edit(content="❌ ไม่สามารถดึงข้อมูลราคาปิดได้ครับ")
                return

            close_prices = all_close.iloc[-2:]
            volume_data = all_volume.iloc[-1]
            
            pct_change = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
            
            market_summary = pd.DataFrame({
                'Ticker': pct_change.index,
                'Price': all_close.iloc[-1],
                'Change (%)': pct_change,
                'Volume': volume_data
            }).dropna()

            # Summary statistics
            gainers = (market_summary['Change (%)'] > 0).sum()
            losers = (market_summary['Change (%)'] < 0).sum()
            avg_change = market_summary['Change (%)'].mean()
            
            # Top N lists
            top_gainers = market_summary.sort_values(by='Change (%)', ascending=False).head(top_n)
            top_losers = market_summary.sort_values(by='Change (%)', ascending=True).head(top_n)
            most_active = market_summary.sort_values(by='Volume', ascending=False).head(top_n)

            # Create embed
            embed_color = discord.Color.green() if avg_change >= 0 else discord.Color.red()
            embed = discord.Embed(
                title="📊 สรุปข้อมูลตลาดหุ้นวันนี้ (S&P 500)",
                description=f"ข้อมูลล่าสุดเมื่อ: {datetime.date.today().strftime('%d/%m/%Y')}",
                color=embed_color
            )
            
            embed.add_field(name="ภาพรวม S&P 500", value=(
                f"หุ้นบวก: `{gainers}` รายการ\n"
                f"หุ้นลบ: `{losers}` รายการ\n"
                f"ค่าเฉลี่ย: `{avg_change:.2f}%`"
            ), inline=False)

            def create_list_string(df, col_name='Change (%)'):
                s = ""
                for index, row in df.iterrows():
                    sign = "+" if row['Change (%)'] >= 0 else ""
                    val = f"{sign}{row[col_name]:.2f}%" if col_name == 'Change (%)' else f"{row[col_name]:,}"
                    s += f"**{row['Ticker']}** - ${row['Price']:.2f} ({val})\n"
                return s if s else "N/A"

            embed.add_field(name=f"📈 หุ้นที่ขึ้นมากที่สุด (Top {top_n})", value=create_list_string(top_gainers), inline=True)
            embed.add_field(name=f"📉 หุ้นที่ลงมากที่สุด (Top {top_n})", value=create_list_string(top_losers), inline=True)
            embed.add_field(name=f"🔥 หุ้นที่มีการซื้อขายมากที่สุด (Top {top_n})", value=create_list_string(most_active, col_name='Volume'), inline=False)
            
            embed.set_footer(text="ข้อจำกัด: ข้อมูลนี้มาจาก S&P 500 เท่านั้น และอาจดีเลย์")

            await ctx.edit(content="", embed=embed)
            logger.info(f"Market data sent successfully")

        except Exception as e:
            logger.error(f"Error in /marketdata: {e}", exc_info=True)
            await ctx.edit(content=f"เกิดข้อผิดพลาดขณะสรุปข้อมูลตลาดครับ: {e}")
    
    logger.info("Market command registered")
