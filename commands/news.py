"""
News command
Display latest news for a stock with Thai translation
"""
import discord
from discord.commands import slash_command, Option
import yfinance as yf
import datetime
from utils.logger import setup_logger
from utils.translator import translate_to_thai
from config import Config

logger = setup_logger(__name__)


def setup(bot: discord.Bot):
    """Register news command with the bot"""
    
    @bot.slash_command(name="news", description="ดึงข่าวสารล่าสุด 5 รายการสำหรับหุ้นตัวนั้น")
    async def news(
        ctx,
        symbol: Option(str, "สัญลักษณ์หุ้น (เช่น AAPL, HIVE)", required=True),
        limit: Option(int, "จำนวนข่าว (สูงสุด 10)", default=5, max_value=10, min_value=1)
    ):
        """Get latest news for a stock"""
        logger.info(f"/news {symbol} command used by {ctx.author}")
        await ctx.defer()

        try:
            ticker = yf.Ticker(symbol.upper())
            news_list = ticker.news

            if not news_list:
                await ctx.respond(f"❌ ไม่พบข่าวสำหรับ '{symbol}' ครับ")
                return

            embed = discord.Embed(
                title=f"📰 ข่าวล่าสุดสำหรับ {symbol.upper()}",
                color=discord.Color.blue()
            )

            count = 0
            for item in news_list:
                if count >= limit:
                    break
                
                content = item.get('content', {})
                
                title = content.get('title', 'ไม่มีหัวข้อ')
                summary = content.get('summary', '')
                publisher = content.get('provider', {}).get('displayName', 'N/A')
                
                # Translate title and summary
                title_th = translate_to_thai(title) if title else 'ไม่มีหัวข้อ'
                summary_th = translate_to_thai(summary) if summary else ''
                
                # Get URL
                link = None
                click_url = content.get('clickThroughUrl')
                if click_url and isinstance(click_url, dict):
                    link = click_url.get('url')
                
                if not link:
                    canonical_url = content.get('canonicalUrl')
                    if canonical_url and isinstance(canonical_url, dict):
                        link = canonical_url.get('url')
                
                if not link:
                    link = content.get('previewUrl')
                
                if not link:
                    link = '#'
                
                if not title_th or str(title_th).strip() == '':
                    continue
                
                title_th = str(title_th)
                link = str(link) if link else '#'
                publisher = str(publisher) if publisher else 'N/A'
                
                # Parse publish time
                publish_time = "N/A"
                pub_date = content.get('pubDate') or content.get('displayTime')
                if pub_date:
                    try:
                        dt = datetime.datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        publish_time = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        publish_time = "N/A"

                description = f"**สำนักข่าว:** {publisher}\n**เวลาเผยแพร่:** {publish_time}\n"
                if summary_th:
                    description += f"{summary_th[:200]}...\n"
                
                # Get thumbnail
                thumbnail_url = None
                thumbnail = content.get('thumbnail')
                if thumbnail and isinstance(thumbnail, dict):
                    resolutions = thumbnail.get('resolutions', [])
                    if resolutions and len(resolutions) > 0:
                        thumbnail_url = resolutions[0].get('url')
                    elif thumbnail.get('originalUrl'):
                        thumbnail_url = thumbnail.get('originalUrl')
                
                display_title = title_th[:250] + "..." if len(title_th) > 250 else title_th
                
                try:
                    if count == 0 and thumbnail_url:
                        embed.set_thumbnail(url=thumbnail_url)
                    
                    embed.add_field(
                        name=f"▶️ {display_title}",
                        value=f"{description}[🔗 อ่านข่าวเต็ม]({link})",
                        inline=False
                    )
                    count += 1
                except Exception as field_error:
                    logger.warning(f"Skipped news item: {field_error}")
                    continue
            
            if count == 0:
                await ctx.respond(f"❌ ไม่พบข่าวที่สามารถแสดงผลได้สำหรับ '{symbol}' ครับ\nอาจจะเป็นเพราะ Yahoo Finance ไม่มีข่าวสำหรับหุ้นตัวนี้ในตอนนี้")
                return
                
            embed.set_footer(text=f"แสดง {count} รายการล่าสุด")
            await ctx.respond(embed=embed)
            logger.info(f"News sent for {symbol}, {count} items")

        except Exception as e:
            logger.error(f"Error in /news {symbol}: {e}", exc_info=True)
            await ctx.respond(f"เกิดข้อผิดพลาดขณะดึงข่าว {symbol} ครับ: {e}")
    
    logger.info("News command registered")
