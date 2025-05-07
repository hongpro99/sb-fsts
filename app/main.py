import uuid
from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import date, datetime, timedelta
import asyncio
import requests
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import numpy as np
from io import StringIO
import boto3
from botocore.client import Config

from app.model.simulation_trading_model import SimulationTradingModel
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

@app.post("/stock/simulate/single")
async def simulate_single_trade(data: SimulationTradingModel):
    
    simulation_data = data.model_dump(exclude_none=True)

    auto_trading_stock = AutoTradingBot(id=simulation_data["user_id"], virtual=False)
    start_date = datetime.fromisoformat(simulation_data["start_date"])
    end_date = datetime.fromisoformat(simulation_data["end_date"])

    data_df, trading_history, trade_reasons = auto_trading_stock.simulate_trading(
        symbol=simulation_data["symbol"],
        start_date=start_date,
        end_date=end_date,
        target_trade_value_krw=simulation_data["target_trade_value_krw"],
        buy_trading_logic=simulation_data["buy_trading_logic"],
        sell_trading_logic=simulation_data["sell_trading_logic"],
        interval=simulation_data["interval"],
        buy_percentage=simulation_data["buy_percentage"],
        ohlc_mode = simulation_data["ohlc_mode"],
        rsi_buy_threshold= simulation_data['rsi_buy_threshold'],
        rsi_sell_threshold= simulation_data['rsi_sell_threshold'],
        rsi_period= simulation_data['rsi_period'],
        initial_capital = simulation_data['initial_capital'],
        use_take_profit=simulation_data["use_take_profit"],
        take_profit_ratio=simulation_data["take_profit_ratio"],
        use_stop_loss=simulation_data["use_stop_loss"],
        stop_loss_ratio=simulation_data["stop_loss_ratio"]
    )

    csv_url = save_df_to_s3(data_df, bucket_name="sb-fsts")
    print(csv_url)
    # data_df_cleaned = data_df.replace([np.inf, -np.inf], np.nan).fillna(0)
    # data_df_cleaned = data_df.replace([np.inf, -np.inf], np.nan)

    response_dict = {
        "data_url": csv_url,
        # "data_df": data_df_cleaned.to_dict(orient="records") if hasattr(data_df_cleaned, "to_dict") else data_df_cleaned,
        "trading_history": trading_history,
        "trade_reasons": trade_reasons
    }

    return response_dict

@app.get("/health")
async def health_check():
    print('health!!')
    return {"status": "healthy!!"}


def save_df_to_s3(data_df, bucket_name, folder_prefix="simulation-results/"):
    # CSV로 변환 (메모리 상에서)
    csv_buffer = StringIO()
    data_df.to_csv(csv_buffer, index=False)

    # key = "20250507"
    key = uuid.uuid4()
    # S3 경로 생성
    s3_key = f"{folder_prefix}{key}.csv"
    
    s3_client = boto3.client('s3', endpoint_url='https://s3.ap-northeast-2.amazonaws.com')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=csv_buffer.getvalue()
    )

    # Presigned URL 생성 (유효시간 1시간)
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': s3_key},
        ExpiresIn=3600
    )
    return presigned_url