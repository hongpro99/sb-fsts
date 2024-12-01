import uuid
from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import datetime
import json
import requests
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone


app = FastAPI()
# api 별 router 등록

@app.get("/health")
async def health_check():
    return {"status": "healthy!!"}