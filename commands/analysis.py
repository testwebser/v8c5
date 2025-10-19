"""
Stock analysis commands: DCA and Probability Analysis
Advanced analysis tools for investment strategies
"""
import discord
from discord.commands import slash_command, Option
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import datetime
from scipy.stats import norm, skew, kurtosis
from utils.logger import setup_logger

logger = setup_logger(__name__)


def setup(bot: discord.Bot):
    """Register analysis commands with the bot"""
    
    @bot.slash_command(name="dca", description="วิเคราะห์กลยุทธ์ DCA (Dollar Cost Averaging)")
    async def dca(
        ctx,
        symbol: Option(str, "สัญลักษณ์หุ้น", required=True),
        amount: Option(float, "จำนวนเงินลงทุนต่องวด (USD)", required=True),
        frequency: Option(str, "ความถี่", choices=["รายวัน", "รายสัปดาห์", "รายเดือน"], required=True),
        period: Option(int, "ระยะเวลาย้อนหลัง (เดือน)", required=True)
    ):
        """DCA strategy analysis"""
        logger.info(f"/dca {symbol} command used by {ctx.author}")
        await ctx.defer()
        
        try:
            end_date = datetime.date.today()
            start_date = end_date - pd.DateOffset(months=period)
            ticker_data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if ticker_data.empty:
                await ctx.respond(f"❌ ไม่พบข้อมูลราคาย้อนหลังสำหรับ '{symbol}' ในช่วง {period} เดือนครับ")
                return
            
            # Fix MultiIndex if present
            if isinstance(ticker_data.columns, pd.MultiIndex):
                ticker_data.columns = ticker_data.columns.droplevel(1)
            
            dca_investments = []
            if frequency == "รายเดือน": 
                freq_code = 'MS'
            elif frequency == "รายสัปดาห์": 
                freq_code = 'W-MON'
            else: 
                freq_code = 'B'
                
            investment_dates = pd.date_range(start=start_date, end=end_date, freq=freq_code)
            total_investment = 0
            total_shares = 0
            
            for date in investment_dates:
                date_ts = pd.Timestamp(date)
                pos = ticker_data.index.searchsorted(date_ts)
                
                if pos >= len(ticker_data):
                    continue
                
                actual_date = ticker_data.index[pos]
                price = ticker_data.loc[actual_date, 'Close']
                shares_bought = amount / price
                total_shares += shares_bought
                total_investment += amount
                
                dca_investments.append({
                    'Date': actual_date, 
                    'Price': price, 
                    'Amount': amount, 
                    'Shares': shares_bought,
                    'TotalShares': total_shares, 
                    'TotalCost': total_investment,
                    'PortfolioValue': total_shares * price
                })

            if not dca_investments:
                await ctx.respond(f"❌ ไม่สามารถจำลองการลงทุนสำหรับ '{symbol}' ได้")
                return

            df = pd.DataFrame(dca_investments)
            final_price = ticker_data.iloc[-1]['Close']
            final_value = total_shares * final_price
            profit_loss = final_value - total_investment
            roi_percent = (profit_loss / total_investment) * 100
            avg_cost_per_share = total_investment / total_shares
            
            embed = discord.Embed(
                title=f"DCA Analysis: {symbol.upper()}",
                description=f"จำลองการลงทุน {frequency} ครั้งละ **${amount:,.2f}** เป็นเวลา **{period} เดือน**",
                color=discord.Color.green() if profit_loss >= 0 else discord.Color.red()
            )
            embed.add_field(name="💰 ข้อมูลการลงทุน", 
                          value=f"เงินลงทุนรวม: `${total_investment:,.2f}`\nจำนวนครั้ง: `{len(df)} ครั้ง`\nระยะเวลา: `{period} เดือน`", 
                          inline=True)
            embed.add_field(name="📊 ผลลัพธ์ DCA", 
                          value=f"มูลค่าพอร์ต: `${final_value:,.2f}`\nกำไร/ขาดทุน: `${profit_loss:,.2f}`\n**ROI: `{roi_percent:.2f}%`**", 
                          inline=True)
            embed.add_field(name="📈 สถิติและราคา", 
                          value=f"ราคาเฉลี่ย DCA: `${avg_cost_per_share:,.2f}`\nราคาปัจจุบัน: `${final_price:,.2f}`\nจำนวนหุ้น: `{total_shares:.4f}`", 
                          inline=False)

            # Create chart
            plt.style.use('dark_background')
            fig, ax1 = plt.subplots(figsize=(10, 6))
            color = 'tab:green'
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Portfolio Value ($)', color=color)
            ax1.plot(df['Date'], df['PortfolioValue'], color=color, label='Portfolio Value')
            ax1.tick_params(axis='y', labelcolor=color)
            ax2 = ax1.twinx()
            color = 'tab:cyan'
            ax2.set_ylabel(f'{symbol.upper()} Price ($)', color=color)
            ax2.plot(ticker_data.index, ticker_data['Close'], color=color, label=f'{symbol} Price', alpha=0.6, linestyle='--')
            ax2.tick_params(axis='y', labelcolor=color)
            plt.title(f'DCA Portfolio Value vs. {symbol.upper()} Price')
            fig.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            discord_file = discord.File(buf, filename=f"dca_{symbol.lower()}.png")
            embed.set_image(url=f"attachment://dca_{symbol.lower()}.png")
            await ctx.respond(file=discord_file, embed=embed)
            logger.info(f"DCA analysis sent for {symbol}")

        except Exception as e:
            logger.error(f"Error in /dca {symbol}: {e}", exc_info=True)
            await ctx.respond(f"เกิดข้อผิดพลาดขณะวิเคราะห์ DCA {symbol} ครับ: {e}")

    @bot.slash_command(name="probability", description="วิเคราะห์การกระจายตัวของผลตอบแทนและความเสี่ยง")
    async def probability(
        ctx,
        symbol: Option(str, "สัญลักษณ์หุ้น", required=True),
        period: Option(str, "ระยะเวลาย้อนหลัง", choices=["6 เดือน", "1 ปี", "2 ปี", "5 ปี"], default="1 ปี")
    ):
        """Probability and risk analysis"""
        logger.info(f"/probability {symbol} command used by {ctx.author}")
        await ctx.defer()

        try:
            period_map = {
                "6 เดือน": "6mo",
                "1 ปี": "1y",
                "2 ปี": "2y",
                "5 ปี": "5y"
            }
            hist_period = period_map.get(period, "1y")

            ticker_data = yf.Ticker(symbol).history(period=hist_period)
            if ticker_data.empty:
                await ctx.respond(f"❌ ไม่พบข้อมูลราคาย้อนหลังสำหรับ '{symbol}' ในช่วง {period} ครับ")
                return
                
            daily_returns = ticker_data['Close'].pct_change().dropna()

            mean_return = daily_returns.mean()
            std_dev = daily_returns.std()
            skewness = skew(daily_returns)
            kurt = kurtosis(daily_returns)
            
            confidence_level = 0.95
            z_score = norm.ppf(1 - confidence_level)
            var_95 = (mean_return + z_score * std_dev)
            cvar_95 = daily_returns[daily_returns <= var_95].mean()
            
            embed = discord.Embed(
                title=f"Probability Analysis: {symbol.upper()}",
                description=f"วิเคราะห์จากข้อมูลย้อนหลัง **{period}** (จำนวน `{len(daily_returns)}` วันเทรด)",
                color=discord.Color.purple()
            )
            
            embed.add_field(name="📊 สถิติพื้นฐาน", value=(
                f"ราคาปิดล่าสุด: `${ticker_data['Close'].iloc[-1]:.2f}`\n"
                f"ราคาเฉลี่ย {period}: `${ticker_data['Close'].mean():.2f}`"
            ), inline=False)
            
            embed.add_field(name="📈 การกระจายผลตอบแทน", value=(
                f"ผลตอบแทนเฉลี่ยต่อวัน: `{mean_return * 100:.2f}%`\n"
                f"ความผันผวน (Std Dev): `{std_dev * 100:.2f}%`\n"
                f"ความเบ้ (Skewness): `{skewness:.3f}`\n"
                f"ความโด่ง (Kurtosis): `{kurt:.3f}`"
            ), inline=True)
            
            embed.add_field(name="🚨 การวัดความเสี่ยง (95%)", value=(
                f"VaR (95%): `{var_95 * 100:.2f}%`\n"
                f"Expected Shortfall: `{cvar_95 * 100:.2f}%`\n"
                f"โอกาสกำไร (รายวัน): `{len(daily_returns[daily_returns > 0]) / len(daily_returns) * 100:.1f}%`"
            ), inline=True)
            
            embed.set_footer(text=f"VaR 95% = มีโอกาส 5% ที่จะขาดทุนมากกว่า {abs(var_95 * 100):.2f}% ใน 1 วัน")

            # Create histogram
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 6))

            n, bins, patches = ax.hist(daily_returns, bins=50, alpha=0.75, label='Daily Returns Distribution')
            
            for i in range(len(patches)):
                if bins[i] < 0:
                    patches[i].set_facecolor('tab:red')
                else:
                    patches[i].set_facecolor('tab:green')

            ax.axvline(mean_return, color='yellow', linestyle='dashed', linewidth=2, label=f'Mean ({mean_return*100:.2f}%)')
            ax.axvline(var_95, color='orange', linestyle='dashed', linewidth=2, label=f'VaR 95% ({var_95*100:.2f}%)')

            ax.set_xlabel('Daily Returns')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Probability Distribution: {symbol.upper()} ({period})')
            
            vals = ax.get_xticks()
            ax.set_xticklabels([f'{x*100:.1f}%' for x in vals])
            
            ax.legend()
            fig.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            discord_file = discord.File(buf, filename=f"prob_{symbol.lower()}.png")
            embed.set_image(url=f"attachment://prob_{symbol.lower()}.png")
            
            await ctx.respond(file=discord_file, embed=embed)
            logger.info(f"Probability analysis sent for {symbol}")

        except Exception as e:
            logger.error(f"Error in /probability {symbol}: {e}", exc_info=True)
            await ctx.respond(f"เกิดข้อผิดพลาดขณะวิเคราะห์ Probability {symbol} ครับ: {e}")
    
    logger.info("Analysis commands registered")
