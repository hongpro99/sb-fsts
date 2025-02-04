from app.utils.technical_indicator import TechnicalIndicator

# 보조지표 클래스 선언
indicator = TechnicalIndicator()
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

    def rsi_trading(self, rsi_values, buy_threshold= 35, sell_threshold= 70):
        """
        RSI를 기반으로 매수/매도 신호를 계산하는 함수.
        
        Args:
            closes (list): 종가 데이터
            window (int): RSI 계산에 사용할 기간
        
        Returns:
            tuple: (buy_signals, sell_signals)
        """
        current_rsi = rsi_values[-1]
        previous_rsi = rsi_values[-2] if len(rsi_values) > 1 else None
        
        if len(rsi_values) < 2 or current_rsi is None or previous_rsi is None:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False, False

            # 매수 신호: RSI가 35 아래에서 35 위로 돌파
        buy_signal = previous_rsi < buy_threshold <= current_rsi

            # 매도 신호: RSI가 70 위에서 70 아래로 하락
        sell_signal = previous_rsi > sell_threshold >= current_rsi
            
        return buy_signal, sell_signal

    def engulfing(self, candle, d_1, d_2, closes):
        """
        상승장악형1 매매 로직.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :param d_2: D-2 캔들 데이터
        :return: 매수 신호 (True/False)
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

        # D-2 조건: 음봉
        d_2_condition = d_2.close < d_2.open

        # D-1 조건: 상승 반전 및 장악형 패턴
        d_1_condition = (
            d_1.open < d_2.low and  # D-1 시가가 D-2 저가보다 낮음
            d_1.close > d_2.high   # D-1 종가가 D-2 고가보다 높음
        )

        # 매수 신호: 현재 캔들이 D-1의 고가를 돌파
        buy_signal = candle.close > d_1.high 

        # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120
        else:
            downward_condition = False
        # 모든 조건 충족 여부 확인
        all_conditions_met = d_2_condition and d_1_condition and downward_condition

        # 매수 신호 반환
        return all_conditions_met and buy_signal

    def penetrating(self, candle, d_1, d_2, closes):
        """
        관통형 로직으로 매수/매도 신호를 판단.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :param d_2: D-2 캔들 데이터
        :return: 매수 신호, 손절 신호, 익절 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

        # D-2 조건: 큰 음봉
        d_2_condition = d_2.close < d_2.open
        d_2_long_bear = abs(d_2.close - d_2.open) >= (float(d_2.open) * 0.02)

        # D-1 조건: 상승 반전
        d_1_condition = (
            d_1.open < d_2.low and
            d_1.close > d_2.close + (d_2.open - d_2.close) / 2
        )
        # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120
        else:
            downward_condition = False
        
        
        # 매수 신호
        buy_signal = candle.close > d_1.high and candle.close> d_2.high
        all_conditions_met = d_2_condition and d_2_long_bear and d_1_condition and downward_condition
        # 손절 신호와 익절 신호는 `simulate_trading`에서 판단
        return all_conditions_met and buy_signal

    def engulfing2(self, candle, d_1, closes):
        """
        상승장악형2 매매 로직.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :return: 매수 신호 (True/False)
        """
        if not d_1:
            # D-1 데이터가 없으면 신호 없음
            return False

        # D-1 조건: 음봉 (종가 < 시가)
        d_1_condition = d_1.close < d_1.open
        
                # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120 
        else:
            downward_condition = False

        # 매수 신호 조건: 현재 캔들의 시가 < D-1 최저가 AND 현재 캔들의 종가 > D-1 최고가
        buy_signal = candle.open < d_1.low and candle.close > d_1.high

        # 모든 조건 충족 확인
        return d_1_condition and buy_signal and downward_condition
    
    def counterattack(self, candle, d_1, d_2, closes):
        """
        상승 반격형 매매 로직.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :param d_2: D-2 캔들 데이터
        :return: 매수 신호 (True/False)
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

        # D-2 조건: 음봉
        d_2_condition = d_2.close < d_2.open

        # D-1 조건: D-1 종가가 D-2 종가와 중간값(midpoint) 이상
        midpoint = d_2.close + (d_2.open - d_2.close) / 2
        d_1_condition = (
            d_1.open < d_2.low and  # D-1 시가가 D-2 저가보다 낮음
            d_1.close >= midpoint   # D-1 종가가 D-2 종가와 midpoint 이상
        )
        # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120
        else:
            downward_condition = False
        # 매수 신호: 현재 캔들의 종가가 D-2의 고가를 돌파
        buy_signal = candle.close > d_2.high
        all_conditions_met = d_2_condition and d_1_condition and downward_condition
        # 모든 조건 충족 여부 확인
        return all_conditions_met and buy_signal


    def harami(self, candle, d_1, d_2, closes):
        """
        상승 잉태형 매매 로직.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :param d_2: D-2 캔들 데이터
        :return: 매수 신호 (True/False)
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

        # D-2 조건: 음봉
        d_2_condition = d_2.close < d_2.open

        # D-1 조건: 잉태형 패턴
        d_1_condition = (
            d_1.close > d_2.close >= d_1.open and  # D-1 종가가 D-2 종가 이상
            d_1.high < d_2.open and  # D-1 고가가 D-2 시가보다 낮음
            d_1.low > d_2.close     # D-1 저가가 D-2 종가보다 높음
        )
        # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120
        else:
            downward_condition = False
        # 매수 신호 조건: 현재 캔들의 종가가 D-2의 고가를 돌파
        buy_signal = candle.close > d_2.high
        all_conditions_met = d_2_condition and d_1_condition and downward_condition
        # 모든 조건 충족 여부 확인
        return all_conditions_met and buy_signal

    def doji_star(self, candle, d_1, d_2, closes):
        """
        상승 도지 스타 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

            # D-2 조건: D-2 종가 < D-2 시초가 (음봉)
        d_2_condition = d_2.close < d_2.open
        # D-1 조건
        d_1_condition = (
                d_1.close == d_1.open and  # 도지 조건
                d_1.open < d_2.low         # D-1 시초가 < D-2 최저가
            )
            # 매수 조건: 당일 종가 > D-2 최고가
        # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120
        else:
            downward_condition = False            
        buy_signal = candle.close > d_2.high
        all_conditions_met = d_2_condition and d_1_condition and downward_condition
        
        return all_conditions_met and buy_signal
    
    def morning_star(self, candle, d_1, d_2, closes):
        """
        샛별형 로직으로 매수/매도 신호를 판단.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :param d_2: D-2 캔들 데이터
        :return: 매수 신호, 손절 신호, 익절 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

        # D-2 조건: 큰 음봉
        d_2_condition = d_2.close < d_2.open #D-2음봉
        d_2_long_bear = abs(d_2.close - d_2.open) >= (float(d_2.open) * 0.02) #장대음봉

        # D-1 조건
        d_1_condition = (
            d_2.close > d_1.close > d_1.open  # D-2 종가 > D-1 종가 > D-1 시초가
        )
        # 당일 조건: 장 양봉
        d_day_condition = (candle.close > candle.open) and abs(candle.close - candle.open) >= (float(candle.open) * 0.02) #장대양봉
        # 60일 이동평균 계산
        sma_60 = indicator.cal_ma(closes, 60)  # 현재 60일 이동평균
        sma_60_prev = indicator.cal_ma(closes[:-1], 60)  # 이전 60일 이동평균 (현재 종가 제외)
        sma_120 = indicator.cal_ma(closes, 120) #120일 이동평균균

        if sma_60 is not None and sma_60_prev is not None and sma_120 is not None: 
            downward_condition = sma_60 <= sma_60_prev and sma_60 <= sma_120
        else:
            downward_condition = False        
        # 매수 신호
        buy_signal =  candle.low > d_1.close and candle.close> d_2.high #buy_signal 연결 or
        all_conditions_met = d_2_condition and d_2_long_bear and d_1_condition and d_day_condition and downward_condition
        # 손절 신호와 익절 신호는 `simulate_trading`에서 판단
        return all_conditions_met and buy_signal

    def down_engulfing(self, candle, d_1, d_2):
        """
        하락장악형 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

            # D-2 조건: D-2 종가 > D-2 시초가 (음봉)
        d_2_condition = d_2.close > d_2.open
        # D-1 조건
        d_1_condition = (
            d_1.open > d_2.high and d_1.close < d_2.low

            )
            # 매수 조건건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_1.low
        all_conditions_met = d_2_condition and d_1_condition
        
        return all_conditions_met and sell_signal
    
    def down_engulfing2(self, candle, d_1):
        """
        하락장악형2 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

        # D-1 조건
        d_1_condition = (
            d_1.close > d_1.open

            )
            # 매수 조건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_1.low and candle.open < d_1.low
        all_conditions_met = d_1_condition
        
        return all_conditions_met and sell_signal
    
    def down_counterattack(self, candle, d_1, d_2):
        """
        하락반격형 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

            # D-2 조건: D-2 종가 > D-2 시초가 (음봉)
        d_2_condition = d_2.close > d_2.open
        # D-1 조건
        d_1_condition = (
            d_1.open > d_2.high
            and d_2.close >= d_1.close >= d_2.open + (d_2.close-d_2.open) / 2

            )
            # 매수 조건건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_2.low
        all_conditions_met = d_2_condition and d_1_condition
        
        return all_conditions_met and sell_signal
    
    def down_harami(self, candle, d_1, d_2):
        """
        하락잉태형 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

            # D-2 조건: D-2 종가 > D-2 시초가 (음봉)
        d_2_condition = d_2.close > d_2.open
        # D-1 조건
        d_1_condition = (
            d_1.open >= d_1.close
            and d_1.high < d_2.close
            and d_1.low > d_2.open

            )
            # 매수 조건건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_2.low
        all_conditions_met = d_2_condition and d_1_condition
        
        return all_conditions_met and sell_signal
    
    def down_doji_star(self, candle, d_1, d_2):
        """
        하락도지스타 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False

            # D-2 조건: D-2 종가 > D-2 시초가 (음봉)
        d_2_condition = d_2.close > d_2.open
        # D-1 조건
        d_1_condition = (
            d_1.open > d_2.high
            and d_1.close == d_1.open
        )
        
        # 매수 조건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_2.low
        all_conditions_met = d_2_condition and d_1_condition
        
        return all_conditions_met and sell_signal
    
    def evening_star(self, candle, d_1, d_2):
        """
        석별형 매도 로직.
        
        Args:
            d_2: D-2일 캔들 데이터 (open, high, low, close 속성 포함).
            d_1: D-1일 캔들 데이터 (open, high, low, close 속성 포함).
            current_candle: 현재 캔들 데이터 (open, high, low, close 속성 포함).
        
        Returns:
            bool: 매도 신호 (sell_signal).
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False
        # D-2 조건: D-2 종가 > D-2 시가 (장대양봉, +2% 이상 상승)
        d_2_condition = (
            d_2.close > d_2.open and  # 양봉
            abs(d_2.close - d_2.open) >= (float(d_2.open) * 0.02)  # 2% 이상 상승
        )
        
        # D-1 조건: D-1 종가 < D-1 시가, D-1 종가 > D-2 종가
        d_1_condition = (
            d_1.close < d_1.open and  # D-1 종가 < D-1 시가
            d_1.close > d_2.close    # D-1 종가 > D-2 종가
        )
        
        # 당일 조건: 장 음봉
        d_day_condition = (candle.close < candle.open) and abs(candle.close - candle.open) >= (float(candle.open) * 0.02) #장대음봉 #2%이상 하락      
        # 매매 시점 조건
        sell_signal = (candle.high < d_1.close 
        and candle.close < candle.low)  # 현재 종가 < 현재 저가
        
        # 최종 매도 신호
        all_conditions_met = d_2_condition and d_1_condition and d_day_condition
        
        return all_conditions_met and sell_signal


    def dark_cloud(self, candle, d_1, d_2):
        """
        흑운형 매도 로직.
        
        Args:
            d_2: D-2일 캔들 데이터 (open, high, low, close 속성 포함).
            d_1: D-1일 캔들 데이터 (open, high, low, close 속성 포함).
            current_candle: 현재 캔들 데이터 (open, high, low, close 속성 포함).
        
        Returns:
            bool: 매도 신호 (sell_signal).
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False
        # D-2 조건: D-2 종가 > D-2 시가 (장대양봉, +2% 이상 상승)
        d_2_condition = (
            d_2.close > d_2.open and  # 양봉
            abs(d_2.close - d_2.open) >= (float(d_2.open) * 0.02)  # 2% 이상 상승
        )
        
        # D-1 조건: D-1 시가 > D-2 고가, D-1 종가 범위: D-1 종가 <= D-1 시가 + (D-2 종가 - D-2 시가) / 2
        midpoint = d_2.open + (d_2.close - d_2.open) / 2
        d_1_condition = (
            d_1.open > d_2.high and
            d_1.close <= midpoint
        )
        
        # 매매 시점: 현재 캔들의 종가 < D-1 저가 또는 현재 캔들의 종가 < D-1 저가
        sell_signal = candle.close < d_1.low and candle.close < candle.low
        
        # 모든 조건 충족 여부
        all_conditions_met = d_2_condition and d_1_condition
        
        return all_conditions_met and sell_signal
    
    def mfi_trading(self, mfi_values):
        """
        MFI를 기반으로 매수/매도 신호를 계산하는 함수.
        """
        # ✅ MFI 값이 None이면 기본값으로 빈 리스트 처리
        if mfi_values is None or not isinstance(mfi_values, list):
            return False, False  # 매수/매도 없음
        
        current_mfi = mfi_values[-1] 
        previous_mfi = mfi_values[-2] if len(mfi_values) > 1 else None
        
        if len(mfi_values) < 0 or current_mfi is None or previous_mfi is None:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False, False

            # 매수 신호: mfi가 20 이하일때 매수
        buy_signal = previous_mfi < 20 <= current_mfi

            # 매도 신호: mfi가 80 이상일때 매도
        sell_signal = previous_mfi > 80 >= current_mfi
            
        return buy_signal, sell_signal
        
    def macd_trading(self, df, current_day):
        """
        특정 날짜(current_day)에 대해 MACD 매매 신호를 반환하는 함수.
        
        :param df: MACD 및 Signal 값이 포함된 데이터프레임
        :param current_day: 현재 시뮬레이션이 진행 중인 날짜 (index로 지정)
        :return: 'Buy' 또는 'Sell' 신호 반환 (True/False)
        """
        # 현재 날짜 인덱스가 데이터에 존재하는지 확인
        if current_day not in df.index:
            return False, False  # 매수, 매도 신호 없음

        # 날짜의 이전 값 확인 (첫 번째 데이터는 신호 없음)
        idx = df.index.get_loc(current_day)
        if idx == 0:
            return False, False

        # MACD & Signal 값 가져오기 (전날과 비교)
        prev_macd = df['macd'].iloc[idx - 1]
        prev_signal = df['macd_signal'].iloc[idx - 1]
        prev_macd_zero = df['macd'].iloc[idx - 1] < 0

        macd = df['macd'].iloc[idx]
        signal = df['macd_signal'].iloc[idx]
        macd_zero = df['macd'].iloc[idx] > 0

        # 📌 매수 신호 조건
        macd_cross_up = prev_macd < prev_signal and macd > signal  # MACD 골든 크로스
        macd_zero_cross_up = prev_macd_zero and macd_zero  # MACD 0선 상향 돌파
        buy_signal = macd_cross_up and macd_zero_cross_up

        # 📌 매도 신호 조건
        macd_cross_down = prev_macd > prev_signal and macd < signal  # MACD 데드 크로스
        macd_zero_cross_down = not prev_macd_zero and not macd_zero  # MACD 0선 하향 돌파
        sell_signal = macd_cross_down and macd_zero_cross_down
        return buy_signal, sell_signal       
        
    