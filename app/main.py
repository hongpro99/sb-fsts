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

# 스케줄러 설정(병렬로 실행)
scheduler = BackgroundScheduler(timezone=timezone('Asia/Seoul'))

#3분 간격으로 실행
scheduler.add_job(auto_trading_scheduler.scheduled_trading_bnuazz15bot_real_task, 'cron', day_of_week='mon-fri', hour='15', minute='15')# 월~금 3시 10분에 실행
scheduler.add_job(auto_trading_scheduler.scheduled_trading_schedulerbot_task, 'cron', day_of_week='mon-fri', hour='15', minute='10')  # 월~금 3시 10분에 실행
scheduler.add_job(auto_trading_scheduler.scheduled_trading_dreaminmindbot_task, 'cron', day_of_week='mon-fri', hour='15', minute='10')  # 월~금 3시 10분에 실행
#scheduler.add_job(auto_trading_scheduler.scheduled_trading_id2_task, 'cron', day_of_week='mon-fri', hour='15', minute='10')  # 월~금 10시 10분에 실행
scheduler.add_job(auto_trading_scheduler.scheduled_trading_bnuazz15bot_task, 'cron', day_of_week='mon-fri', hour='15', minute='04') # 월~금 3시 10분에 실행
#scheduler.add_job(auto_trading_scheduler.scheduled_trading_weeklybot_task, 'cron', day_of_week='fri', hour='15', minute='10')# 금 3시 10분에 실행(주봉)


scheduler.start()

@app.get("/trade")
async def trade():

    auto_trading_scheduler.scheduled_trading()

    return {"status": "trade 완료!!!"}


@app.get("/health")
async def health_check():
    print('health!!')
    return {"status": "healthy!!"}