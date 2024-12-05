import uuid
from fastapi import FastAPI
from datetime import datetime, date
import uvicorn
from app.utils.factory import create_auto_trading_stock
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# 환경 변수 파일 로드
load_dotenv()

# 봇 토큰 가져오기
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 봇 프리픽스 설정 (명령어 앞에 붙는 문자열, 예: "!help")
BOT_PREFIX = "!"

# 봇 초기화
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True  # 서버 관련 이벤트 접근
intents.members = True  # 멤버 정보 접근 (Server Members Intent 활성화)
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# 글로벌 변수로 AutoTradingStock 객체를 저장
auto_trading = None

# 봇 이벤트: 준비 완료
# @bot.event
# async def on_ready():
#     # 특정 채널에 메시지 보내기
#     channel_id = '1314162472235831336' #메시지를 보낼 채널 ID
#     channel = bot.get_channel(channel_id)
    
#     if channel:
#         channel.send("👋 안녕하세요! 저는 트레이딩 봇입니다.\n"
#                         "모의투자 또는 실전투자를 선택해 트레이딩을 시작하세요.\n"
#                         "명령어를 입력하거나 자세한 내용을 확인하려면 도움말을 참조하세요.")
#     else:
#         print("지정된 채널을 찾을 수 없습니다.")
        
# 명령어: 모의투자 여부 입력받기
@bot.command(name="select")
async def select_account(ctx):
    global auto_trading

    await ctx.send("📊 모의투자를 사용하시겠습니까? (y/n):")

    # 사용자의 응답을 기다림
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)  # 30초 대기
        user_choice = msg.content.strip().lower()

        if user_choice in ["y", "n"]:
            auto_trading = create_auto_trading_stock(user_choice)
            account_type = "모의투자" if user_choice == "y" else "실전투자"

            # 성공 메시지 및 인증 정보 디스코드로 전송
            await ctx.send(f"✅ {account_type} 계좌가 선택되었습니다.")
            auth_info = auto_trading.get_auth_info()
            await ctx.send(f"📋 인증 정보: {auth_info}")
        else:
            await ctx.send("⚠️ 잘못된 입력입니다. 'y' 또는 'n'을 입력해주세요.")
    except Exception as e:
        await ctx.send(f"❌ 오류 발생: {e}")

# 명령어: 트레이딩 시뮬레이션 실행
@bot.command(name="simulate")
async def simulate_trading(ctx):
    global auto_trading

    if auto_trading is None:
        await ctx.send("⚠️ 먼저 'select' 명령어로 계좌를 선택해주세요.")
        return

    symbol = "035420"  # Naver
    start_date = date(2023, 1, 1)
    end_date = date(2024, 1, 1)
    target_trade_value_krw = 1000000

    await ctx.send(f"📈 트레이딩 시뮬레이션을 시작합니다. 종목: {symbol}, 기간: {start_date} ~ {end_date}")

    try:
        # 트레이딩 시뮬레이션 실행
        simulation_plot, realized_pnl, current_pnl = auto_trading.simulate_trading(
            symbol, start_date, end_date, target_trade_value_krw
        )

        # 시뮬레이션 결과 출력
        await ctx.send(f"✅ 트레이딩 시뮬레이션 완료!\n"
                    f"실현 손익: {realized_pnl:.2f} KRW\n"
                    f"현재 평가 손익: {current_pnl:.2f} KRW")

        # 차트를 저장하고 디스코드에 업로드
        chart_path = f"{symbol}_trading_chart.png"
        simulation_plot[0].savefig(chart_path)
        simulation_plot[0].clf()  # 메모리 해제를 위해 차트 초기화
        await ctx.send(file=discord.File(chart_path))

    except Exception as e:
        await ctx.send(f"❌ 트레이딩 시뮬레이션 중 오류 발생: {e}")

# 봇 실행
if __name__ == "__main__":
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"❌ 봇 실행 중 오류 발생: {e}")
