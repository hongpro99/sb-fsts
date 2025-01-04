from datetime import datetime, date, timedelta
import requests

from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor
from app.utils.auto_trading_bot import AutoTradingBot

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
    
    # TO-DO
    # 매수 로직 여기에 추가
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