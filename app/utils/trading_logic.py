class TradingLogic:

    # 체결 강도 기준 매매 대상인지 확인
    def func1(self):
        # 체결 강도 조건 확인
        
        return True / False
    

    # 윗꼬리와 아랫꼬리를 체크하는 함수
    def check_wick(self, candle, previous_closes, lower_band, sma, upper_band):
        open_price = float(candle.open)
        high_price = float(candle.high)
        low_price = float(candle.low)
        close_price = float(candle.close)

        # 윗꼬리 아랫꼬리 비율
        wick_ratio = 1.3

        # 볼린저 밴드 및 시간 정보
        middle_band = sma
        print(f"시간: {candle.time}, open_price: {open_price:.0f} KRW, low_price: {low_price:.0f} KRW, high_price: {high_price:.0f} KRW, close_price: {close_price:.0f} KRW, 볼린저 밴드 정보: 상단: {upper_band:.0f} KRW, 중단: {middle_band:.0f} KRW, 하단: {lower_band:.0f} KRW")

        # 아랫꼬리 여부 (고가와 저가의 차이가 크고 양봉일 때, 하락 중에만, 볼린저 밴드 하단 근처에서)
        lower_wick = min(open_price, close_price) - low_price # 아랫꼬리
        upper_wick = high_price - max(open_price, close_price) # 윗꼬리

        body = abs(open_price - close_price)
        # body 에 2배한게 꼬리보다 클 때 
        body_ratio = 2

        average_previous_close = sum(previous_closes) / len(previous_closes) if previous_closes else close_price
        
        is_downtrend = close_price < average_previous_close
        is_near_lower_band = low_price <= (lower_band + (lower_band * 0.01)) and open_price < middle_band # 볼린저 밴드 하단 근처 및 하단 이하에서만 인식
        # 아랫꼬리가 윗꼬리보다 클때, 양봉일 때, 하락 중에만, 볼린저 밴드 하단 근처에서, body * n 이 꼬리보다 클 때  
        # has_lower_wick = lower_wick > body * 0.3 and close_price > open_price and is_downtrend and is_near_lower_band
        has_lower_wick = abs(lower_wick) > abs(upper_wick) * wick_ratio and close_price > open_price and is_downtrend and is_near_lower_band and body * body_ratio > abs(upper_wick)

        print(f'윗꼬리 = {upper_wick}, 아랫꼬리 = {lower_wick}, body = {body}')

        if not has_lower_wick:
            reason = []
            if abs(lower_wick) <= abs(upper_wick):
                reason.append("아랫꼬리가 윗꼬리보다 짦음")
            if close_price <= open_price:
                reason.append("종가가 시가보다 높지 않음")
            if not is_downtrend:
                reason.append("하락 추세가 아님")
            if not is_near_lower_band:
                reason.append("볼린저 밴드 하단 근처가 아님")
            if body * body_ratio <= abs(upper_wick):
                reason.append(f"윗꼬리가 바디 * {body_ratio} 보다 김")
            print(f"아랫꼬리 감지 실패: 시간: {candle.time}, 사유: {', '.join(reason)}")

        if has_lower_wick:
            print(f"아랫꼬리 감지: 시간: {candle.time}, close_price: {close_price:.7f} KRW, 볼린저 밴드 상단: {upper_band:.7f} KRW, 중단: {middle_band:.7f} KRW, 하단: {lower_band:.7f} KRW")

        # 윗꼬리 여부 (고가와 저가의 차이가 크고 음봉일 때, 상승 중에만, 볼린저 밴드 상단 근처에서)
        is_uptrend = close_price > average_previous_close
        is_near_upper_band = high_price >= (upper_band - (upper_band * 0.01)) and open_price > middle_band # 볼린저 밴드 상단 근처 및 상단 이상에서만 인식
        # 윗꼬리가 아랫꼬리보다 클 때, 음봉일 때, 상승 중에만, 볼린저 밴드 상단 근처에서, body * n 이 꼬리보다 클 때  
        has_upper_wick = abs(upper_wick) > abs(lower_wick) * wick_ratio and close_price < open_price and is_uptrend and is_near_upper_band and body * body_ratio > abs(lower_wick)

        if not has_upper_wick:
            reason = []
            if abs(upper_wick) <= abs(lower_wick):
                reason.append("윗꼬리가 아랫꼬리보다 짦음")
            if close_price >= open_price:
                reason.append("종가가 시가보다 낮지 않음")
            if not is_uptrend:
                reason.append("상승 추세가 아님")
            if not is_near_upper_band:
                reason.append("볼린저 밴드 상단 근처가 아님")
            if body * body_ratio <= abs(lower_wick):
                reason.append(f"아랫꼬리가 바디 * {body_ratio} 보다 김")
            print(f"윗꼬리 감지 실패: 시간: {candle.time}, 사유: {', '.join(reason)}")

        if has_upper_wick:
            print(f"윗꼬리 감지: 시간: {candle.time}, close_price: {close_price:.7f} KRW, 볼린저 밴드 상단: {upper_band:.7f} KRW, 중단: {middle_band:.7f} KRW, 하단: {lower_band:.7f} KRW")

        return has_upper_wick, has_lower_wick

    # def __init__(self, ohlc):
    #     """
    #     초기화 메소드.
    #     :param ohlc: 날짜별 OHLC 데이터 (KisDomesticDailyChartBar 객체 리스트)
    #     """
    #     self.ohlc = ohlc

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
    
    def engulfing_logic2(self):
        """
        상승장악형2 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        results = []
        successful_trades = []

        if len(self.ohlc) < 2:
            raise ValueError("2일 이상의 데이터가 필요합니다.")

        for i in range(1, len(self.ohlc)):
            d_1 = self.ohlc[i - 1]  # D-1 데이터
            current = self.ohlc[i]  # 당일 데이터

            # D-1 조건: D-1 종가 < D-1 시초가 (음봉)
            d_1_condition = d_1.close < d_1.open
            print(f"\n[D-1 조건] 날짜: {d_1.time}")
            print(f"  종가 < 시초가: {d_1.close} < {d_1.open} = {d_1_condition}")

            # 매매 시점 조건
            buy_signal = current.open < d_1.low and current.close > d_1.high
            print(f"\n[매매 시점] 날짜: {current.time}")
            print(f"  당일 시가 < D-1 최저가: {current.open} < {d_1.low} = {current.open < d_1.low}")
            print(f"  당일 종가 > D-1 최고가: {current.close} > {d_1.high} = {current.close > d_1.high}")

            # 손절 조건
            stoploss = current.close < d_1.low
            print(f"\n[손절 조건] 날짜: {current.time}")
            print(f"  종가 < D-1 최저가: {current.close} < {d_1.low} = {stoploss}")

            # 모든 조건 충족 여부 확인
            all_conditions_met = d_1_condition
            print(f"\n[전체 조건 충족 여부] 날짜: {current.time}")
            print(f"  D-1 조건: {d_1_condition}")
            print(f"  모든 조건 충족: {all_conditions_met}")

            if all_conditions_met:
                if buy_signal:
                    trade_result = {
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승장악형2",
                        "매매시점": "SS < L and P > H",
                        "손절조건": "미충족" if not stoploss else "충족",
                        "매수 성공 여부": "성공",
                    }
                    results.append(trade_result)
                    successful_trades.append(trade_result)
                else:
                    results.append({
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승장악형2",
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
    
    def counterattack_logic(self):
        """
        상승 반격형 매매 로직.
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

            # D-2 조건
            d_2_condition = d_2.close < d_2.open

            # D-1 조건
            midpoint = d_2.close + (d_2.open - d_2.close) / 2
            d_1_condition = (
                d_1.open < d_2.low and
                d_2.close <= d_1.close >= midpoint
            )

            # 매매 시점
            buy_signal = current.close > d_2.high

            # 손절 조건
            stoploss = current.close < d_2.low

            # 모든 조건 충족 여부 확인
            all_conditions_met = d_2_condition and d_1_condition

            if all_conditions_met:
                if buy_signal:
                    trade_result = {
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승 반격형",
                        "매매시점": "P > h",
                        "손절조건": "미충족" if not stoploss else "충족",
                        "매수 성공 여부": "성공",
                    }
                    results.append(trade_result)
                    successful_trades.append(trade_result)
                else:
                    results.append({
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승 반격형",
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

    def harami_logic(self):
        """
        상승 잉태형 매매 로직.
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

            # D-2 조건
            d_2_condition = d_2.close < d_2.open

            # D-1 조건
            d_1_condition = (
                d_1.close > d_2.close >= d_1.open and
                d_1.high < d_2.open and
                d_1.low > d_2.close
            )

            # 매매 시점
            buy_signal = current.close > d_2.high

            # 손절 조건
            stoploss = current.close < d_2.low

            # 모든 조건 충족 여부 확인
            all_conditions_met = d_2_condition and d_1_condition

            if all_conditions_met:
                if buy_signal:
                    trade_result = {
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승 잉태형",
                        "매매시점": "P > h",
                        "손절조건": "미충족" if not stoploss else "충족",
                        "매수 성공 여부": "성공",
                    }
                    results.append(trade_result)
                    successful_trades.append(trade_result)
                else:
                    results.append({
                        "날짜": current.time,
                        "매수/매도": "매수신호",
                        "특징": "상승 잉태형",
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

