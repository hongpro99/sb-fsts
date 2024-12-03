#app의 entrypoint 역할을 하는 파일(실행파일)
#utils에 있는 파일들을 임포트하여 사용

import uuid
from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import date, time
import json
import requests
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from app.utils.auto_trading_stock import AutoTradingStock
import uvicorn
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np

app = FastAPI()

# AutoTradingStock 클래스 초기화
auto_trading = AutoTradingStock()


symbol = '035420' # naver

start_date = date(2023, 1, 1)
end_date = date(2024, 1, 1)

target_trade_value_krw = 1000000  # 매수 목표 거래 금액


print(f"트레이딩 시뮬레이션을 시작합니다. 종목: {symbol}, 기간: {start_date} ~ {end_date}")

try:
        # 트레이딩 시뮬레이션 실행
        simulation_plot, realized_pnl, current_pnl = auto_trading.simulate_trading(
            symbol, start_date, end_date, target_trade_value_krw
        )

        # 시뮬레이션 결과 출력
        print(f"실현 손익: {realized_pnl:.2f} KRW")
        print(f"현재 평가 손익: {current_pnl:.2f} KRW")

        # 차트를 파일로 저장
        chart_path = f"{symbol}_trading_chart.png"
        simulation_plot[0].savefig(chart_path)
        simulation_plot[0].clf()  # 메모리 해제를 위해 차트 초기화

        # Discord로 결과 전송
        message = (
            f"📊 트레이딩 시뮬레이션 완료!\n"
            f"종목 코드: {symbol}\n"
            f"시작 날짜: {start_date}\n"
            f"끝 날짜: {end_date}\n"
            f"실현 손익: {realized_pnl:.2f} KRW\n"
            f"현재 평가 손익: {current_pnl:.2f} KRW"
        )
        auto_trading.send_discord_webhook(message, "trading", file_path=chart_path)

        print(f"시뮬레이션 결과가 Discord에 전송되었습니다.")

except Exception as e:
        print(f"트레이딩 시뮬레이션 중 오류 발생: {e}")


@app.get("/health")  # health 경로로 들어오는 GET 요청을 처리하는 엔드포인트
async def health_check():
    # Discord Webhook 메시지 전송
    message = "📢 서버 상태 점검: 서버가 정상적으로 실행 중입니다!"
    bot_type = "trading"
    auto_trading.send_discord_webhook(message, bot_type)
    
    # 응답 반환
    return {"status": "healthy!!"}

@app.get("/trade_status")
async def trade_status():
    # 예제: 트레이딩 상태 확인 및 Webhook 전송
    message = "📈 현재 트레이딩 상태를 확인 중입니다."
    bot_type = "trading"
    auto_trading.send_discord_webhook(message, bot_type)
    
    return {"status": "trading_status_requested"}

@app.post("/simulate")
async def simulate_trading(symbol: str, start_date: str, end_date: str, target_trade_value_krw: int):
    """
    트레이딩 시뮬레이션 실행 및 Discord Webhook 전송
    """
    try:
        # 시뮬레이션 실행
        simulation_plot, realized_pnl, current_pnl = auto_trading.simulate_trading(
            symbol, start_date, end_date, target_trade_value_krw
        )

        # 차트를 파일로 저장
        chart_path = f"{symbol}_trading_chart.png"
        simulation_plot[0].savefig(chart_path)
        simulation_plot[0].clf()  # 메모리 해제를 위해 차트 초기화

        # 결과 메시지 작성
        message = (
            f"📊 트레이딩 시뮬레이션 완료!\n"
            f"종목 코드: {symbol}\n"
            f"시작 날짜: {start_date}\n"
            f"끝 날짜: {end_date}\n"
            f"실현 손익: {realized_pnl:.2f} KRW\n"
            f"현재 평가 손익: {current_pnl:.2f} KRW"
        )

        # Discord로 결과 전송
        auto_trading.send_discord_webhook(message, "trading", file_path=chart_path)

        # 저장한 차트 파일 삭제
        import os
        if os.path.exists(chart_path):
            os.remove(chart_path)

        # 성공 응답 반환
        return {"status": "success", "message": "트레이딩 시뮬레이션이 성공적으로 실행되고 Discord에 전송되었습니다."}

    except Exception as e:
        # 오류 발생 시 HTTPException 반환
        raise HTTPException(status_code=500, detail=f"시뮬레이션 실행 중 오류 발생: {str(e)}")

    
# 서버 실행 엔트리 포인트
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)