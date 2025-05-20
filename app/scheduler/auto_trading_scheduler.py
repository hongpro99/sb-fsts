from datetime import datetime, date, timedelta
import requests
import json
import math

from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor
from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.dynamodb.model.stock_symbol_model import StockSymbol
from app.utils.dynamodb.model.user_info_model import UserInfo
from pykis import KisBalance
from app.utils.webhook import Webhook
# db = get_db()
sql_executor = SQLExecutor()
#보조지표 클래스
webhook = Webhook()

def scheduled_trading_schedulerbot_task():
    scheduled_trading(id='schedulerbot', virtual= False, trading_bot_name = 'schedulerbot')

# def scheduled_trading_id1_task():
#     scheduled_trading(id="id1")

def scheduled_trading_dreaminmindbot_task():
    scheduled_trading(id='id1', virtual = False, trading_bot_name = 'dreaminmindbot')

def scheduled_trading_bnuazz15bot_task():
    scheduled_trading(id='bnuazz15', virtual = True, trading_bot_name = 'bnuazz15bot')
    
def scheduled_trading_weeklybot_task():
    scheduled_trading(id='weeklybot', virtual = True, trading_bot_name = 'weeklybot')
    
def scheduled_trading_bnuazz15bot_real_task():
    scheduled_trading(id='bnuazz15bot_real', virtual = False, trading_bot_name = 'bnuazz15bot_real')


def scheduled_trading(id, virtual = False, trading_bot_name = 'schedulerbot'):
    
    # TO-DO
    # 잔고 조회 여기에 추가
    trading_bot = AutoTradingBot(id=id, virtual=virtual)
    print(f"{trading_bot_name}의 자동 트레이딩을 시작합니다")

    # 당일로부터 1년전 기간으로 차트 분석
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    interval = "day"
    
        # ✅ 코스닥150 종목 가져오기
    result = list(StockSymbol.scan(
        filter_condition=(StockSymbol.type == 'kosdaq150')
    ))

    # ✅ 거래대금 기준 정렬 함수
    def get_estimated_trade_value(stock):
        try:
            symbol = stock.symbol

            # OHLC 데이터 가져오기 (최신 종가용)
            ohlc_data = trading_bot._get_ohlc(symbol, start_date, end_date, interval)
            if not ohlc_data:
                print(f"❌ {symbol} OHLC 데이터 없음")
                return -1

            # 가장 마지막 종가
            last_candle = ohlc_data[-1]
            close_price = last_candle.close

            # 외국인+기관 순매수 기반 거래대금 계산
            trade_value = trading_bot.calculate_trade_value_from_fake_qty(
                api_response=None,  # 내부에서 API 호출함
                close_price=close_price,
                symbol=symbol
            )

            print(f"📊 {stock.symbol_name} | 종가: {close_price:,} | 예상 거래대금: {trade_value:,}원")
            return trade_value
        except Exception as e:
            print(f"❌ {stock.symbol} 거래대금 계산 실패: {e}")
            return -1

    # ✅ 거래대금 기준 내림차순 정렬
    sorted_result = sorted(
        result,
        key=lambda stock: get_estimated_trade_value(stock),
        reverse=True
    )

    print(f"sorted_result : {sorted_result}")
    print(f"개수 : {len(sorted_result)}")
    
    #target_trade_value_krw = 100000
    
    # 매수 목표 거래 금액
    trading_bot_name = trading_bot_name
    #interval = 'day'

    # 특정 trading_bot_name의 데이터 조회, 임시로
    history = UserInfo.query(id) # schedulerbot은 왜 id 대신 직접 schedulerbot을 넣어야 하는가?


    for trade in history:
        print(f"- buy_trading_logic: {trade.buy_trading_logic}, sell_trading_logic : {trade.sell_trading_logic}")

        buy_trading_logic = trade.buy_trading_logic
        sell_trading_logic = trade.sell_trading_logic
        target_trade_value_krw = trade.target_trade_value_krw
        max_allocation = trade.max_allocation
        interval = trade.interval
        take_profit_threshold = trade.take_profit_threshold
        stop_loss_threshold = trade.stop_loss_threshold
        use_stop_loss = trade.use_stop_loss
        use_take_profit = trade.use_take_profit
        
        
    # ✅ scheduled_trading 시작 시 잔고 조회
    account = trading_bot.kis.account()
    balance: KisBalance = account.balance()

    for holding in balance.stocks:
        symbol = holding.symbol

        # ✅ 매입금액 0인 경우 방어 처리
        if holding.purchase_amount == 0:
            print(f"🚫 {symbol} - 매입금액 0원: 손익률 계산 생략")
            continue  # 그냥 이 종목은 패스

        profit_rate = float(holding.profit_rate)

        final_sell_yn = False
        reason = None

        if use_take_profit and profit_rate >= take_profit_threshold:
            final_sell_yn = True
            reason = "익절"
        elif use_stop_loss and profit_rate <= -stop_loss_threshold:
            final_sell_yn = True
            reason = "손절"

        if final_sell_yn :
            try:
                print(f"✅ {symbol} {reason} 조건 충족 -> 매도 실행 ")
                trading_bot._trade_place_order(
                    symbol=symbol,
                    symbol_name=symbol,
                    target_trade_value_krw=None,
                    order_type="sell",
                    max_allocation=1,
                    trading_bot_name=trading_bot_name,
                    
                )
            except Exception as e:
                print(f"❌ {symbol} 매도 실패: {e}")
                    
    print(f'------ {trading_bot_name}의 계좌 익절/손절이 완료되었습니다. 이제부터 주식 자동 트레이딩을 시작합니다!')            
    webhook.send_discord_webhook(
    f'----------------------- {trading_bot_name}의 계좌 익절/손절이 완료되었습니다. 이제부터 주식 자동 트레이딩을 시작합니다!',
    "trading"
    )
    #✅ enumerate로 종목 번호 부여 (1부터 시작)
    for i, stock in enumerate(sorted_result, start=1):
        symbol = stock.symbol
        original_symbol_name = stock.symbol_name
        symbol_name = f"[{i}]{original_symbol_name}"  # 종목명에 번호 붙이기

        max_retries = 5
        retries = 0

        print(f'------ {trading_bot_name}의 {symbol_name} 주식 자동 트레이딩을 시작합니다. ------')

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
                    max_allocation = max_allocation,
                    take_profit_threshold = take_profit_threshold,
                    stop_loss_threshold = stop_loss_threshold,
                    use_stop_loss = use_stop_loss,
                    use_take_profit= use_take_profit
                )
                break
            except Exception as e:
                retries += 1
                print(f"Error occurred while trading {symbol_name} (Attempt {retries}/{max_retries}): {e}")
                if retries >= max_retries:
                    print(f"Skipping {symbol_name} after {max_retries} failed attempts.")
                    
    trading_bot._upsert_account_balance(trading_bot_name) # 따로 스케줄러 만들어서 다른 시간에 하도록 설정해도 됨
    trading_bot.update_roi(trading_bot_name) # 따로 스케줄러 만들어서 다른 시간에 하도록 설정해도 됨


def scheduled_single_buy_task():
    """
    테스트용: 특정 종목 1주 자동 매수 (시장가)
    """

    # ✅ 인스턴스 생성
    trading_bot = AutoTradingBot(id="schedulerbot", virtual=False)

    # ✅ 매수할 종목 정보 (원하는 종목으로 변경 가능)
    symbol = "300720"        # 삼성전자
    target_trade_value_krw = 10000000

    quote = trading_bot._get_quote(symbol=symbol)
    #qty = math.floor(target_trade_value_krw / quote.close) # 주식 매매 개수
    qty = 1
    buy_price = None         # 시장가 매수 (지정가 입력 시 가격 설정)
    sell_price = None
    symbol_name = '한일시멘트'
    
    print(f"[{datetime.now()}] 자동 매수 실행: 종목 {symbol}, 수량 {qty}주")

    try:
        trading_bot.place_order(
            symbol=symbol,
            qty=qty,
            symbol_name = symbol_name,
            sell_price=sell_price,   # 시장가 매수
            order_type="sell"
        )
    except Exception as e:
        print(f"❌ 매수 실패: {e}")