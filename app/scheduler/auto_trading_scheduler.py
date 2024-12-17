from datetime import datetime
import requests

from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor

# db = get_db()
sql_executor = SQLExecutor()


def send_discord_webhook(message, bot_type):
    if bot_type == 'trading':
        webhook_url = 'https://discord.com/api/webhooks/1313346849838596106/6Rn_8BNDeL9bMYfFtqscpu4hPah5c2RsNl0rBiPoSw_Qb9RXgDdVHoHmwEuStPv_ufnV'  # 복사한 Discord 웹훅 URL로 변경
        username = "Stock Trading Bot"

    data = {
        "content": message,
        "username": username,  # 원하는 이름으로 설정 가능
    }
    
    # 요청 보내기
    response = requests.post(webhook_url, json=data)
    
    # 응답 확인
    if response.status_code == 204:
        print("메시지가 성공적으로 전송되었습니다.")
    else:
        print(f"메시지 전송 실패: {response.status_code}, {response.text}")


def scheduled_trading_task():
    
    message = "매수가 완료되었습니다."
    bot_type = "trading"

    send_discord_webhook(message, bot_type)