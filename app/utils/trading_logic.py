from datetime import datetime, timedelta

class TradingLogic:
    def __init__(self, ohlc_data):
        self.ohlc_data = ohlc_data

    def _find_data_by_offset(self, base_date, offset):
        """
        기준 날짜(base_date)로부터 offset일 전 데이터를 반환.
        """
        target_date = base_date - timedelta(days=offset)

        # 데이터 검색
        for data in self.ohlc_data:
            if data.time.date() == target_date.date():  # datetime 객체 비교
                return data
        return None

    def get_open(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.open if data else None

    def get_close(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.close if data else None

    def get_high(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.high if data else None

    def get_low(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.low if data else None


def check_trading_signal(condition, base_date):
    """
    매수 신호를 체크하는 함수.
    조건:
    1. D-2 장대음봉: 시초가와 종가 차이가 3% 이상이며 e < s
    2. D-1 조건: S < l, E > e + (s - e) / 2
    3. 매매 시점: P > h
    4. 손절 조건: P < L
    """

    # D-2 데이터
    s = condition.get_open(base_date, 2)
    e = condition.get_close(base_date, 2)

    # D-1 데이터
    S = condition.get_open(base_date, 1)
    E = condition.get_close(base_date, 1)
    h = condition.get_high(base_date, 1)
    l = condition.get_low(base_date, 1)

    # 당일 데이터
    SS = condition.get_open(base_date, 0)
    P = condition.get_close(base_date, 0)

    # D-2 조건 체크
    if s is None or e is None:
        return "데이터 부족 (D-2)"
    d2_condition = (abs(s - e) / s >= 0.03) and (e < s)

    # D-1 조건 체크
    if S is None or E is None or h is None or l is None:
        return "데이터 부족 (D-1)"
    d1_condition = (S < l) and (E > e + (s - e) / 2)

    # 매매 조건 체크
    if SS is None or P is None:
        return "데이터 부족 (당일)"
    buy_signal = d2_condition and d1_condition and (P > h)

    # 손절 조건 체크
    stop_loss = P < l

    # 결과 반환
    if buy_signal:
        return "매수 신호 발생"
    elif stop_loss:
        return "손절 조건 발생"
    else:
        return "조건 미충족"