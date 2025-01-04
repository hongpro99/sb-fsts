# tradinglogic.py
class TradingLogic:
    def __init__(self, ohlc):
        """
        초기화 메소드.
        :param ohlc: 날짜별 OHLC 데이터 (KisDomesticDailyChartBar 객체 리스트)
        """
        self.ohlc = ohlc

    def engulfing_logic(self):
        """
        상승장악형1 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        results = []
        successful_trades = []

        if len(self.ohlc) < 3:
            raise ValueError("3일 이상의 데이터가 필요합니다.")

        for i in range(2, len(self.ohlc)):
            d_2 = self.ohlc[i - 2]  # D-2 데이터
            d_1 = self.ohlc[i - 1]  # D-1 데이터
            current = self.ohlc[i]  # 당일 데이터

            # D-2 조건 (음봉)
            d_2_condition = d_2.close < d_2.open

            # D-1 조건
            d_1_condition = (
                d_1.open < d_2.low and
                d_1.close > d_2.high
            )

            # 매매 시점
            buy_signal = current.close > d_1.high

            # 손절 조건
            stoploss = current.close < d_1.low

            # 모든 조건 충족 여부 확인
            all_conditions_met = d_2_condition and d_1_condition

            if all_conditions_met:
                if buy_signal:
                    trade_result = {
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승장악형1",
                        "매매시점": "P > H",
                        "손절조건": "미충족" if not stoploss else "충족",
                        "매수 성공 여부": "성공",
                    }
                    results.append(trade_result)
                    successful_trades.append(trade_result)
                else:
                    results.append({
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승장악형1",
                        "매매시점": "미충족",
                        "손절조건": "미충족" if not stoploss else "충족",
                        "매수 성공 여부": "실패",
                    })
            else:
                results.append({
                    "날짜": current.time,
                    "매수/매도": "조건 미충족",
                    "특징": "미충족",
                    "매매시점": "미충족",
                    "손절조건": "미충족",
                    "매수 성공 여부": "실패",
                })

        return results, successful_trades

    def trading_signal_penetrating(self):
        """
        이전 매매 로직 (상승장악형 외의 로직).
        :return: 매수 성공 목록과 개별 신호
        """
        # 이전 로직 구현 (생략 가능)
        results = []
        successful_trades = []

        if len(self.ohlc) < 3:
            raise ValueError("3일 이상의 데이터가 필요합니다.")

        # 로직 예제 (D-2 음봉, D-1 상승, 매매 조건 등)
        for i in range(2, len(self.ohlc)):
            d_2 = self.ohlc[i - 2]
            d_1 = self.ohlc[i - 1]
            current = self.ohlc[i]

            # D-2 조건
            d_2_condition = d_2.close < d_2.open
            d_2_long_bear = abs(d_2.close - d_2.open) >= (float(d_2.open) * 0.03)

            # D-1 조건
            d_1_condition = (
                d_1.open < d_2.low and
                d_1.close > d_2.close + (d_2.open - d_2.close) / 2
            )

            # 매매 시점
            buy_signal = current.close > d_1.high

            # 손절 조건
            stoploss = current.close < d_1.low

            # 모든 조건 충족 여부
            all_conditions_met = d_2_condition and d_2_long_bear and d_1_condition

            if all_conditions_met:
                if buy_signal:
                    trade_result = {
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "기존 로직",
                        "매매시점": "P > H",
                        "손절조건": "미충족" if not stoploss else "충족",
                        "매수 성공 여부": "성공",
                    }
                    results.append(trade_result)
                    successful_trades.append(trade_result)
                else:
                    results.append({
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "기존 로직",
                        "매매시점": "미충족",
                        "손절조건": "미충족",
                        "매수 성공 여부": "실패",
                    })
            else:
                results.append({
                    "날짜": current.time,
                    "매수/매도": "조건 미충족",
                    "특징": "미충족",
                    "매매시점": "미충족",
                    "손절조건": "미충족",
                    "매수 성공 여부": "실패",
                })

        return results, successful_trades
