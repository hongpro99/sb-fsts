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
from app.utils.auto_trading_stock import AutoTradingStock
app = FastAPI()
# .env 파일 로드
load_dotenv()





# auto_trading 객체 초기화
auto_trading = None

try:
        #석문 모의투자 계좌
    auto_trading = AutoTradingStock(
        # HTS 로그인 ID  예) soju06
    id=os.getenv('YOUR_ID'),
        # 앱 키  예) Pa0knAM6JLAjIa93Miajz7ykJIXXXXXXXXXX
    api_key=os.getenv('API_KEY'),
        # 앱 시크릿 키  예) V9J3YGPE5q2ZRG5EgqnLHn7XqbJjzwXcNpvY . . .
    secret_key=os.getenv('API_SECRET'),
        # 앱 키와 연결된 계좌번호  예) 00000000-01
    account=os.getenv('ACCOUNT_NO'),
    virtual=True
    )
    
    print("AutoTradingStock 객체가 정상적으로 생성되었습니다.")
    
    # 생성된 객체의 인증 정보 확인
    auth_info = auto_trading.get_auth_info()
    message = (
        f"{'모의투자' if auth_info['virtual'] else '실전투자'} 계좌가 선택되었습니다.\n"
        f"인증 정보: {auth_info}"
    )
    auto_trading.send_discord_webhook(message, "trading")
    
    # 잔고 조회
    balance_result = auto_trading.inquire_balance()
    if balance_result:
        print("잔고 조회가 성공적으로 완료되었습니다.")
    else:
        print("잔고 조회 실패.")
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
