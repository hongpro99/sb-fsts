# app.py
import uuid
from fastapi import FastAPI
from datetime import date
import uvicorn
from app.utils.factory import create_auto_trading_stock
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

app = FastAPI()
# .env 파일 로드
load_dotenv()

app = FastAPI()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# auto_trading 객체 초기화
auto_trading = None

@bot.event
async def on_ready():
    """봇 준비 완료 이벤트"""
    print(f"{bot.user} 디스코드 봇이 실행 중입니다!")


try:
    # 사용자 입력 기반으로 객체 생성
    auto_trading = create_auto_trading_stock()
    print("AutoTradingStock 객체가 정상적으로 생성되었습니다.")
    
    # 생성된 객체의 인증 정보 확인
    auth_info = auto_trading.get_auth_info()
    message = (
        f"{'모의투자' if auth_info['virtual'] else '실전투자'} 계좌가 선택되었습니다.\n"
        f"인증 정보: {auth_info}"
    )
    auto_trading.send_discord_webhook(message, "trading")
    
    # 디버깅 용
    print(f"인증 정보: {auth_info}")
    
except Exception as e:
    print(f"계좌 선택 과정 중 오류 발생: {e}")
    exit(1)  # 프로그램 종료


symbol = "035420"  # Naver
start_date = date(2023, 1, 1)
end_date = date(2024, 1, 1)
target_trade_value_krw = 1000000

message = f"트레이딩 시뮬레이션을 시작합니다. 종목: {symbol}, 기간: {start_date} ~ {end_date}"

#auto_trading.send_discord_webhook(message, "trading")

try:
    # 트레이딩 시뮬레이션 실행
    simulation_plot, realized_pnl, current_pnl = auto_trading.simulate_trading(
        symbol, start_date, end_date, target_trade_value_krw
    )

    # 시뮬레이션 결과 출력
    print(f"실현 손익: {realized_pnl:.2f} KRW")
    print(f"현재 평가 손익: {current_pnl:.2f} KRW")

except Exception as e:
    print(f"트레이딩 시뮬레이션 중 오류 발생: {e}")




@app.get("/health")
async def health_check():
    message = "📢 서버 상태 점검: 서버가 정상적으로 실행 중입니다!"
    auto_trading.send_discord_webhook(message, "trading")
    return {"status": "healthy"}

# 서버 실행 엔트리 포인트
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
