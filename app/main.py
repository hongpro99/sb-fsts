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

scheduler.add_job(auto_trading_scheduler.scheduled_trading_schedulerbot_task, 'cron', day_of_week='mon-fri', hour='15', minute='15')  # 월~금 3시 15분에 실행
# scheduler.add_job(auto_trading_scheduler.scheduled_trading_id1_task, 'cron', day_of_week='mon-fri', hour='15', minute='10')  # 월~금 10시 10분에 실행
# scheduler.add_job(auto_trading_scheduler.scheduled_trading_id2_task, 'cron', day_of_week='mon-fri', hour='15', minute='10')  # 월~금 10시 10분에 실행
scheduler.add_job(auto_trading_scheduler.scheduled_trading_bnuazz15_task, 'cron', day_of_week='mon-fri', hour='15', minute='05')  # 월~금 3시 5분에 실행
# scheduler.add_job(auto_trading_scheduler.scheduled_single_buy_task, 'cron', hour='20', minute='5')  # 월~금 3시 10분에 실행
# scheduler.add_job(auto_trading_scheduler.scheduled_trading_task, 'cron', day_of_week='mon-fri', hour='20', minute='43')  # 월~금 3시 10분에 실행 

scheduler.start()

@app.get("/trade")
async def trade():

    auto_trading_scheduler.scheduled_trading()

    return {"status": "trade 완료!!!"}


@app.get("/health")
async def health_check():
    print('health!!')
    return {"status": "healthy!!"}