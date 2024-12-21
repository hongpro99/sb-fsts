import uuid
from datetime import date
from app.utils.factory import create_auto_trading_stock
from app.utils.simulation import Simulation
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# 환경 변수 파일 로드
load_dotenv()

# 봇 토큰 가져오기
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 봇 프리픽스 설정
BOT_PREFIX = "!"

# 봇 초기화
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# AutoTradingStock 및 Simulation 객체를 관리하는 클래스
class TradingBotManager:
    def __init__(self):
        self.auto_trading = None
        self.simulation = None

    def initialize_auto_trading(self, account_type: str):
        self.auto_trading = create_auto_trading_stock(account_type)
        self.simulation = Simulation(auto_trading_stock=self.auto_trading)

    def is_initialized(self):
        return self.auto_trading is not None and self.simulation is not None


# 글로벌 객체 생성
manager = TradingBotManager()

# 봇 이벤트: 준비 완료
@bot.event
async def on_ready():
    print(f"✅ 봇이 준비되었습니다. 봇 이름: {bot.user.name}")


# 계좌 선택 명령어
@bot.command(name="select")
async def select_account(ctx):
    await ctx.send("📊 어떤 계좌를 사용하시겠습니까? (real/mock):")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        user_choice = msg.content.strip().lower()

        if user_choice in ["real", "mock"]:
            manager.initialize_auto_trading(user_choice)
            account_type = "모의투자" if user_choice == "mock" else "실전투자"

            await ctx.send(f"✅ {account_type} 계좌가 선택되었습니다.")
            manager.auto_trading.send_account_info_to_discord()
        else:
            await ctx.send("⚠️ 잘못된 입력입니다. 'real' 또는 'mock'을 입력해주세요.")
    except Exception as e:
        await ctx.send(f"❌ 오류 발생: {e}")


# 잔고 조회 명령어
@bot.command(name="balance")
async def balance(ctx):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    try:
        await ctx.send("🔄 잔고 정보를 조회 중입니다...")
        manager.auto_trading.inquire_balance()
    except Exception as e:
        await ctx.send(f"❌ 잔고 조회 중 오류 발생: {e}")


# 거래 시간 조회 명령어
@bot.command(name="trading_hours")
async def get_trading_hours(ctx):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    await ctx.send("🌍 주식 시장 국가 코드를 입력해주세요 (예: US, KR, JP):")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        country_msg = await bot.wait_for("message", check=check, timeout=30)
        country_code = country_msg.content.strip().upper()
        manager.auto_trading.get_trading_hours(country_code)
    except Exception as e:
        await ctx.send(f"❌ 거래 시간 조회 중 오류 발생: {e}")


# 주문 명령어
@bot.command(name="order")
async def place_order(ctx):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        # 주문 종류 입력
        await ctx.send("📊 주문 종류를 선택해주세요 (매수/매도):")
        order_type_msg = await bot.wait_for("message", check=check, timeout=30)
        order_type = order_type_msg.content.strip().lower()

        if order_type not in ["매수", "매도"]:
            await ctx.send("⚠️ 잘못된 입력입니다. '매수' 또는 '매도'를 입력해주세요.")
            return

        # 종목 코드 입력
        await ctx.send("📄 종목 코드를 입력해주세요:")
        symbol_msg = await bot.wait_for("message", check=check, timeout=30)
        symbol = symbol_msg.content.strip()

        # 수량 입력
        await ctx.send("🔢 주문 수량을 입력해주세요:")
        qty_msg = await bot.wait_for("message", check=check, timeout=30)
        qty = int(qty_msg.content.strip())

        # 가격 입력
        await ctx.send("💰 주문 가격을 입력해주세요 (시장가로 주문하려면 '시장가'를 입력하세요):")
        price_msg = await bot.wait_for("message", check=check, timeout=30)
        price_input = price_msg.content.strip()

        # 주문 가격 설정
        buy_price = None
        sell_price = None
        if price_input.lower() != "시장가":
            price = int(price_input)
            buy_price = price if order_type == "매수" else None
            sell_price = price if order_type == "매도" else None

        # 주문 실행
        manager.auto_trading.place_order(
            symbol=symbol,
            qty=qty,
            buy_price=buy_price,
            sell_price=sell_price,
            order_type="buy" if order_type == "매수" else "sell"
        )
        
        # 주문 성공 메시지
        await ctx.send(f"✅ 주문 완료: 종목={symbol}, 수량={qty}, 주문 가격={price_input}, 주문 종류={order_type}")

    except Exception as e:
        # 오류 발생 시 에러 메시지 출력
        await ctx.send(f"❌ 주문 처리 중 오류 발생: {e}")


# 거래량 순위 명령어
@bot.command(name="volumeRanking_trading")
async def volume_ranking_trading(ctx):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    await ctx.send("📊 입력 종목 코드를 입력해주세요 (0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200):")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        market_msg = await bot.wait_for("message", check=check, timeout=30)
        market_code = market_msg.content.strip().upper()

        manager.auto_trading.get_volume_power_ranking_and_trade(market_code)
        await ctx.send(f"✅ {market_code} 시장 거래량 순위를 조회하였습니다.")
    except Exception as e:
        await ctx.send(f"❌ 거래량 순위 조회 중 오류 발생: {e}")


# 배당 순위 명령어
@bot.command(name="dividend_ranking")
async def dividend_ranking(ctx):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    try:
        await ctx.send("🔄 배당률 상위 종목을 조회 중입니다...")
        manager.auto_trading.get_top_dividend_stocks()
        await ctx.send("✅ 배당률 상위 종목 조회를 완료했습니다.")
    except Exception as e:
        await ctx.send(f"❌ 배당률 조회 중 오류 발생: {e}")


# 투자자 매매 동향 명령어
@bot.command(name="investor_trend")
async def investor_trend(ctx):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        await ctx.send("📊 시장 코드를 입력해주세요 (KSP: KOSPI, KSQ: KOSDAQ):")
        market_msg = await bot.wait_for("message", check=check, timeout=30)
        market_code = market_msg.content.strip().upper()

        await ctx.send("📊 업종 코드를 입력해주세요 (0001: KOSPI, 1001:KOSDAQ):")
        industry_msg = await bot.wait_for("message", check=check, timeout=30)
        industry_code = industry_msg.content.strip()

        manager.auto_trading.get_investor_trend(market_code, industry_code)
        await ctx.send(f"✅ 투자자 매매 동향 조회를 완료했습니다.")
    except Exception as e:
        await ctx.send(f"❌ 투자자 매매 동향 조회 중 오류 발생: {e}")
        
        
        
        # 시뮬레이션 명령어
@bot.command(name="simulate") #예: !simulate 035420
async def simulate(ctx, symbol: str):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return


    start_date = date(2023, 1, 1)
    end_date = date(2024, 1, 1)
    target_trade_value_krw = 1_000_000

    await ctx.send(f"{symbol}의 시세입니다. ")
    manager.auto_trading.get_stock_quote(symbol)
    
    await ctx.send(f"📈 {symbol} 종목 시뮬레이션을 시작합니다. 기간: {start_date} ~ {end_date}")
        
    try:    
        
        simulation_plot, realized_pnl, current_pnl = manager.simulation.simulate_trading(
            symbol, start_date, end_date, target_trade_value_krw
        )

        # 결과 출력
        await ctx.send(
            f"✅ 시뮬레이션 완료!\n"
            f"총 실현 손익: {realized_pnl:.2f} KRW\n"
            f"현재 잔고: {current_pnl:.2f} KRW"
        )

        # 차트를 저장하고 업로드
        chart_path = f"{symbol}_trading_chart.png"
        simulation_plot[0].savefig(chart_path)
        await ctx.send(file=discord.File(chart_path))
        os.remove(chart_path)
        
    except Exception as e:
        await ctx.send(f"❌ 시뮬레이션 중 오류 발생: {e}")


# RSI 시뮬레이션 명령어
@bot.command(name="rsi_simulate") #!rsi_trading 005930 2023-01-01 2023-12-31
async def rsi_simulate(ctx, symbol: str, start_date: str, end_date: str):
    if not manager.is_initialized():
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    try:
        await ctx.send(f"📊 RSI 매매 시뮬레이션을 시작합니다. 종목: {symbol}, 기간: {start_date} ~ {end_date}")
        plot, _, _, final_assets, total_pnl = manager.simulation.rsi_simulate_trading(symbol, start_date, end_date)

        # 결과 출력
        await ctx.send(f"✅ RSI 시뮬레이션 완료!\n최종 자산: {final_assets:.2f} KRW\n총 손익: {total_pnl:.2f} KRW")

        # 차트 업로드
        chart_path = f"{symbol}_rsi_simulation.png"
        plot.savefig(chart_path)
        await ctx.send(file=discord.File(chart_path))
        os.remove(chart_path)
    except Exception as e:
        await ctx.send(f"❌ RSI 시뮬레이션 중 오류 발생: {e}")



# 봇 실행
if __name__ == "__main__":
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"❌ 봇 실행 중 오류 발생: {e}")
