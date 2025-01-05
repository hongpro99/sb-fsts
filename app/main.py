import uuid
from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import date, datetime, timedelta
import asyncio
import requests
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from app.scheduler import auto_trading_scheduler
from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor

app = FastAPI() 

# api 별 router 등록

# 스케줄러 설정
scheduler = BackgroundScheduler(timezone=timezone('Asia/Seoul'))

scheduler.add_job(auto_trading_scheduler.scheduled_trading_task, 'cron', day_of_week='mon-fri', hour='15', minute='10')  # 월~금 3시 10분에 실행 

scheduler.start()


@app.get("/trade")
async def trade():

    trading_bot = AutoTradingBot(user_name="홍석형")
    
    sql_executor = SQLExecutor()

    query = """
        SELECT 종목코드, 종목이름 FROM fsts.kospi200;
    """

    params = {
    }

    with get_db_session() as db:
        result = sql_executor.execute_select(db, query, params)
    
    # 당일로부터 1년전 기간으로 차트 분석
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    target_trade_value_krw = 1000000  # 매수 목표 거래 금액

    for stock in result:
        symbol = stock['종목코드']
        symbol_name = stock['종목이름']

        max_retries = 10  # 최대 재시도 횟수
        retries = 0  # 재시도 횟수 초기화

        print(f'------ {symbol_name} 주식 자동 트레이딩을 시작합니다. ------')

        while retries < max_retries:
            try:
                trading_bot.trade(symbol, symbol_name, start_date, end_date, target_trade_value_krw)
                break
            except Exception as e:
                retries += 1
                print(f"Error occurred while trading {symbol_name} (Attempt {retries}/{max_retries}): {e}")
                if retries >= max_retries:
                    print(f"Skipping {symbol_name} after {max_retries} failed attempts.")

    return {"status": "trade 완료!!!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy!!"}