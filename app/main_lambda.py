from datetime import datetime, date, timedelta
import os

from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor
from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.dynamodb.model.stock_symbol_model import StockSymbol
from app.utils.dynamodb.model.user_info_model import UserInfo


def lambda_handler(event, context):
    print("Lambda Docker container is running!")
    id = os.environ.get("ID", "schedulerbot")  # 환경 변수가 없으면 None 반환
    
    scheduled_trading(id)
    
    return {
        "statusCode": 200,
        "body": "Hello from Lambda in Docker!"
    }


def scheduled_trading(id):
    
    # TO-DO
    # 매수 로직 여기에 추가
    trading_bot = AutoTradingBot(id=id)
    
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
        
    for stock in result:
        symbol = stock.symbol
        symbol_name = stock.symbol_name

        max_retries = 5  # 최대 재시도 횟수
        retries = 0  # 재시도 횟수 초기화

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
                    interval=interval
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