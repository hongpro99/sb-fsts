from datetime import date, datetime
from app.utils.stock_auto_trading import AutoTradingStock
from app.utils.trading_logic import TradingLogic, check_trading_signal

# AutoTradingStock 인스턴스 생성
auto_trading_stock = AutoTradingStock()

# 주식 심볼 및 기간 설정
symbol = '352820'
start_date = date(2023, 1, 1)
end_date = date(2024, 1, 1)

# OHLC 데이터 가져오기
ohlc_data_raw = auto_trading_stock._get_ohlc(symbol, start_date, end_date)

# OHLC 데이터를 객체 리스트로 변환
class OHLCData:
    def __init__(self, time, open, high, low, close):
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close


ohlc_data = []
for row in ohlc_data_raw:
    ohlc_data.append(OHLCData(
        time=row.time,   # datetime 객체
        open=row.open,   # 시가
        high=row.high,   # 고가
        low=row.low,     # 저가
        close=row.close  # 종가
    ))

# Condition 객체 생성
condition = TradingLogic(ohlc_data)

# 매수 포지션 상태 저장
position = {
    "is_holding": False,  # 매수 포지션 보유 여부
    "buy_date": None,     # 매수 날짜
    "buy_price": None     # 매수 가격
}

# OHLC 데이터를 기준으로 날짜별 매수/손절 신호 처리
for data in ohlc_data:
    base_date = data.time
    signal = check_trading_signal(condition, base_date)

    if signal == "매수 신호 발생" and not position["is_holding"]:
        # 매수 신호 발생 시 포지션 기록
        position["is_holding"] = True
        position["buy_date"] = base_date
        position["buy_price"] = data.close
        print(f"매수 발생: 날짜={position['buy_date']}, 가격={position['buy_price']}")

    elif signal == "손절 조건 발생" and position["is_holding"]:
        # 손절 조건 발생 시 포지션 해제
        print(f"손절 발생: 날짜={base_date}, 손절 가격={data.close}")
        position["is_holding"] = False
        position["buy_date"] = None
        position["buy_price"] = None

    else:
        # 신호 없음 또는 조건 미충족
        print(f"{base_date}: {signal}")

# 최종 포지션 상태 출력
if position["is_holding"]:
    print(f"최종 포지션 보유: 매수 날짜={position['buy_date']}, 매수 가격={position['buy_price']}")
else:
    print("최종 포지션 없음")
