from datetime import datetime
from app.utils.auto_trading_bot import AutoTradingBot

def scheduled_single_buy_task():
    """
    테스트용: 특정 종목 1주 자동 매수 (시장가)
    """

    # ✅ 인스턴스 생성
    trading_bot = AutoTradingBot(id="id1", virtual=False)

    # ✅ 매수할 종목 정보 (원하는 종목으로 변경 가능)
    symbol = "005930"        # 삼성전자
    qty = 1                  # 수량 1주
    buy_price = None         # 시장가 매수 (지정가 입력 시 가격 설정)

    print(f"[{datetime.now()}] 자동 매수 실행: 종목 {symbol}, 수량 {qty}주")

    try:
        trading_bot.place_order(
            symbol=symbol,
            qty=qty,
            buy_price=buy_price,   # 시장가 매수
            order_type="buy"
        )
    except Exception as e:
        print(f"❌ 매수 실패: {e}")

# 직접 실행 시
if __name__ == "__main__":
    scheduled_single_buy_task()
