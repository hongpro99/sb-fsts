import uuid
from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import datetime
import asyncio
import requests
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from app.scheduler import auto_trading_scheduler
from app.utils.discord_bot import run_discord_bot


app = FastAPI() 

# api 별 router 등록

# 스케줄러 설정
scheduler = BackgroundScheduler(timezone=timezone('Asia/Seoul'))

scheduler.add_job(auto_trading_scheduler.scheduled_trading_task, 'cron', minute='*/15', second='5')  # 매 15분 5초에 실행

scheduler.start()


@app.get("/health")
async def health_check():
    return {"status": "healthy!!"}