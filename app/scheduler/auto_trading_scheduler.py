from datetime import datetime, date, timedelta
import requests
import json
import math

from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor
from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.dynamodb.model.stock_symbol_model import StockSymbol
from app.utils.dynamodb.model.user_info_model import UserInfo

# db = get_db()
sql_executor = SQLExecutor()


def scheduled_trading_schedulerbot_task():
    scheduled_trading(id="schedulerbot", virtual= False, max_allocation = 0.9)

# def scheduled_trading_id1_task():
#     scheduled_trading(id="id1")

# def scheduled_trading_id2_task():
#     scheduled_trading(id="id2")

def scheduled_trading_bnuazz15_task():
    scheduled_trading(id="bnuazz15", virtual = True, max_allocation = 0.01)

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


def scheduled_trading(id, virtual = False, max_allocation = 0.01):
    
    # TO-DO
    # 매수 로직 여기에 추가
    trading_bot = AutoTradingBot(id=id, virtual=virtual)
    
    # sql_executor = SQLExecutor()

    # query = """
    #     SELECT 종목코드, 종목이름 FROM fsts.kospi200;
    # """

    # params = {
    # }

    # with get_db_session() as db:
    #     result = sql_executor.execute_select(db, query, params)

    result = list(StockSymbol.scan(
        filter_condition=((StockSymbol.type == 'kospi200') | (StockSymbol.type == 'kosdaq150'))
    ))
    
    # 당일로부터 1년전 기간으로 차트 분석
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    target_trade_value_krw = 1000000
    
    # 매수 목표 거래 금액
    trading_bot_name = 'test_bot'
    interval = 'day'

    # 특정 trading_bot_name의 데이터 조회
    history = UserInfo.query("schedulerbot")

    for trade in history:
        print(f"- buy_trading_logic: {trade.buy_trading_logic}, sell_trading_logic : {trade.sell_trading_logic}")
        
        buy_trading_logic = trade.buy_trading_logic
        sell_trading_logic = trade.sell_trading_logic
        
    # ✅ enumerate로 종목 번호 부여 (1부터 시작)
    for i, stock in enumerate(result, start=1):
        symbol = stock.symbol
        original_symbol_name = stock.symbol_name
        symbol_name = f"[{i}]{original_symbol_name}"  # 종목명에 번호 붙이기

        max_retries = 5
        retries = 0

        print(f'------ {symbol_name} 주식 자동 트레이딩을 시작합니다. ------')

        while retries < max_retries:
            try:
                trading_bot.trade(
                    trading_bot_name=trading_bot_name,
                    buy_trading_logic=buy_trading_logic,
                    sell_trading_logic=sell_trading_logic,
                    symbol=symbol,
                    symbol_name=symbol_name,
                    start_date=start_date,
                    end_date=end_date,
                    target_trade_value_krw=target_trade_value_krw,
                    interval=interval,
                    max_allocation = max_allocation
                )
                break
            except Exception as e:
                retries += 1
                print(f"Error occurred while trading {symbol_name} (Attempt {retries}/{max_retries}): {e}")
                if retries >= max_retries:
                    print(f"Skipping {symbol_name} after {max_retries} failed attempts.")



def scheduled_single_buy_task():
    """
    테스트용: 특정 종목 1주 자동 매수 (시장가)
    """

    # ✅ 인스턴스 생성
    trading_bot = AutoTradingBot(id="id2", virtual=False)

    # ✅ 매수할 종목 정보 (원하는 종목으로 변경 가능)
    symbol = "054180"        # 삼성전자
    target_trade_value_krw = 300

    quote = trading_bot._get_quote(symbol=symbol)
    #qty = math.floor(target_trade_value_krw / quote.close) # 주식 매매 개수
    qty = 1
    buy_price = None         # 시장가 매수 (지정가 입력 시 가격 설정)
    sell_price = None
    
    print(f"[{datetime.now()}] 자동 매수 실행: 종목 {symbol}, 수량 {qty}주")

    try:
        trading_bot.place_order(
            symbol=symbol,
            qty=qty,
            sell_price=sell_price,   # 시장가 매수
            order_type="sell"
        )
    except Exception as e:
        print(f"❌ 매수 실패: {e}")