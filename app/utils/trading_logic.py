from app.utils.technical_indicator import TechnicalIndicator
import pandas as pd
import io
import numpy as np

# 보조지표 클래스 선언
indicator = TechnicalIndicator()
class TradingLogic:

    def __init__(self):
        self.trade_reasons = []

    # 윗꼬리와 아랫꼬리를 체크하는 함수
    def check_wick(self, candle, previous_closes, symbol, lower_band, sma, upper_band):
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

        reason = []

        if not has_lower_wick:
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

        buy_signal = has_lower_wick
        sell_signal = has_upper_wick

        trade_entry = {
                'symbol': symbol,
                'Time' : candle.time,
                'price' : close_price,
                'upper_wick' : upper_wick,
                'lower_wick' : lower_wick,
                'body' : body,
                'BB upper_band': upper_band,
                'BB middle_band': middle_band,
                'BB lower_band': lower_band,
                'Buy Signal': buy_signal,
                'Sell Signal': sell_signal,
                'Reason': reason
            }
        self.trade_reasons.append(trade_entry)  
        
        return buy_signal, sell_signal

    def rsi_trading(self, candle, rsi_values, symbol, buy_threshold= 30, sell_threshold= 70):
        """
        RSI를 기반으로 매수/매도 신호를 계산하는 함수.
        
        Args:
            closes (list): 종가 데이터
            window (int): RSI 계산에 사용할 기간
        
        Returns:
            tuple: (buy_signals, sell_signals)
        """
        
        # ✅ None 값 제거 (dropna() 대신 직접 필터링)
        rsi_values = [rsi for rsi in rsi_values if rsi is not None]

        # ✅ NaN 제거 후 데이터 확인
        if len(rsi_values) < 2:
            return False, False  # 기본값 반환
        
        previous_rsi = rsi_values[-2]
        current_rsi = rsi_values[-1]
        
        # ✅ 기본값 설정
        buy_signal = False
        sell_signal = False
        reason = ""

        trade_date = candle.time.date()  # 날짜만 추출 (YYYY-MM-DD)
        close_price = float(candle.close)
        volume = candle.volume
        # 📌 매수 신호 판단 (Buy)
        if previous_rsi <= buy_threshold and current_rsi > buy_threshold:
            buy_signal = True
            reason = f"RSI {previous_rsi:.2f} → {current_rsi:.2f} (Buy Threshold {buy_threshold} 초과)"

        # 📌 매도 신호 판단 (Sell)
        elif previous_rsi >= sell_threshold and current_rsi < sell_threshold:
            sell_signal = True
            reason = f"RSI {previous_rsi:.2f} → {current_rsi:.2f} (Sell Threshold {sell_threshold} 하락)"

        # 📌 매수/매도 신호가 없는 경우, 이유 저장
        else:
            if previous_rsi > buy_threshold and current_rsi > buy_threshold:
                reason = ("RSI가 이미 매수 임계값 이상, 추가 매수 없음")
            elif previous_rsi < sell_threshold and current_rsi < sell_threshold:
                reason = ("RSI가 이미 매도 임계값 이하, 추가 매도 없음")
            elif previous_rsi > buy_threshold and current_rsi < buy_threshold:
                reason = ("RSI가 매수 임계값을 초과했으나 다시 하락")
            elif previous_rsi < sell_threshold and current_rsi > sell_threshold:
                reason = ("RSI가 매도 임계값 이하였으나 다시 상승")
            else:
                reason = ("RSI 기준 충족하지 않음")

        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                #entry['Buy Signal'] = buy_signal
                entry['Sell Signal'] = sell_signal
                entry['Reason'] = reason           
            
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
            return False, None

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
        return all_conditions_met and buy_signal, None

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
            return False, None

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
        return all_conditions_met and buy_signal, None

    def engulfing2(self, candle, d_1, closes):
        """
        상승장악형2 매매 로직.
        :param candle: 현재 캔들 데이터
        :param d_1: D-1 캔들 데이터
        :return: 매수 신호 (True/False)
        """
        if not d_1:
            # D-1 데이터가 없으면 신호 없음
            return False, None

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
        return d_1_condition and buy_signal and downward_condition, None
    
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
            return False, None

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
        return all_conditions_met and buy_signal, None


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
            return False, None

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
        return all_conditions_met and buy_signal, None

    def doji_star(self, candle, d_1, d_2, closes):
        """
        상승 도지 스타 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return False, None

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
        
        return all_conditions_met and buy_signal, None
    
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
            return False, None

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
        return all_conditions_met and buy_signal, None

    def down_engulfing(self, candle, d_1, d_2):
        """
        하락장악형 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return None, False

            # D-2 조건: D-2 종가 > D-2 시초가 (음봉)
        d_2_condition = d_2.close > d_2.open
        # D-1 조건
        d_1_condition = (
            d_1.open > d_2.high and d_1.close < d_2.low

            )
            # 매수 조건건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_1.low
        all_conditions_met = d_2_condition and d_1_condition
        
        return None, all_conditions_met and sell_signal
    
    def down_engulfing2(self, candle, d_1):
        """
        하락장악형2 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return None, False

        # D-1 조건
        d_1_condition = (
            d_1.close > d_1.open

            )
            # 매수 조건: 당일 종가 > D-2 최고가
        sell_signal = candle.close < d_1.low and candle.open < d_1.low
        all_conditions_met = d_1_condition
        
        return None, all_conditions_met and sell_signal
    
    def down_counterattack(self, candle, d_1, d_2):
        """
        하락반격형 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return None, False

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
        
        return None, all_conditions_met and sell_signal
    
    def down_harami(self, candle, d_1, d_2):
        """
        하락잉태형 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return None, False

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
        
        return None, all_conditions_met and sell_signal
    
    def down_doji_star(self, candle, d_1, d_2):
        """
        하락도지스타 매매 로직.
        :return: 매수 성공 목록과 개별 신호
        """
        if not d_1 or not d_2:
            # D-1 또는 D-2 데이터가 없으면 신호 없음
            return None, False

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
        
        return None, all_conditions_met and sell_signal
    
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
            return None, False
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
        
        return None, all_conditions_met and sell_signal


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
            return None, False
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
        
        return None, all_conditions_met and sell_signal
    
    def mfi_trading(self, df, symbol, buy_threshold=25, sell_threshold=75):
        """
        ✅ MFI 매매 신호 생성 및 매매 사유 저장
        - MFI < buy_threshold → 매수
        - MFI > sell_threshold → 매도
        """
        
        if df.shape[0] < 2:
            print("❌ MFI 계산을 위한 데이터가 부족합니다.")
            return False, False
        
        # 가장 최근 캔들
        candle = df.iloc[-1]
        trade_date = candle.name.date()  # datetime index에서 날짜 추출
        close_price = float(candle['Close'])
        volume = candle['Volume']
        
        # 현재 및 이전 MFI
        current_mfi = candle['mfi']
        previous_mfi = df['mfi'].iloc[-2]

        # 초기 값
        buy_signal = False
        sell_signal = False
        reason = ""

        # ✅ 매수 조건
        if previous_mfi < buy_threshold and current_mfi > buy_threshold:
            buy_signal = True
            reason = f"MFI {previous_mfi:.2f} → {current_mfi:.2f} (Buy Threshold {buy_threshold} 초과)"

        # ✅ 매도 조건
        elif previous_mfi > sell_threshold and current_mfi < sell_threshold:
            sell_signal = True
            reason = f"MFI {previous_mfi:.2f} → {current_mfi:.2f} (Sell Threshold {sell_threshold} 하락)"

        # ✅ 신호가 없는 경우
        else:
            if previous_mfi > buy_threshold and current_mfi > buy_threshold:
                reason = "MFI가 이미 매수 임계값 이상, 추가 매수 없음"
            elif previous_mfi < sell_threshold and current_mfi < sell_threshold:
                reason = "MFI가 이미 매도 임계값 이하, 추가 매도 없음"
            elif previous_mfi > buy_threshold and current_mfi < buy_threshold:
                reason = "MFI가 매수 임계값 초과 후 다시 하락"
            elif previous_mfi < sell_threshold and current_mfi > sell_threshold:
                reason = "MFI가 매도 임계값 이하 후 다시 상승"
            else:
                reason = "MFI 기준 충족하지 않음"

        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Sell Signal'] = sell_signal
                entry['Reason'] = reason

        return buy_signal, sell_signal
        
    def macd_trading(self, candle, df, symbol):
        """
        ✅ MACD 크로스 & MACD 오실레이터 조합
        - MACD 크로스 신호 + MACD OSC 방향이 일치할 때만 매매
        """

        # 날짜 및 현재 시세 정보
        trade_date = candle.time.date()
        close_price = float(candle.close)
        volume = candle.volume

        # 데이터 충분한지 확인
        if df.shape[0] < 2:
            print("❌ MACD 계산에 필요한 데이터가 부족합니다.")
            return False, False

        # 가장 최근 2개 값
        current_hist = df['macd_histogram'].iloc[-1]
        previous_hist = df['macd_histogram'].iloc[-2]

        # 초기화
        buy_signal = False
        sell_signal = False
        reason = ""

        # ✅ MACD 오실레이터 0선 돌파 조건
        if previous_hist <= 0 and current_hist > 0:
            buy_signal = True
            reason = f"MACD 오실레이터 0선 상향 돌파: {previous_hist:.4f} → {current_hist:.4f}"
        elif previous_hist >= 0 and current_hist < 0:
            sell_signal = True
            reason = f"MACD 오실레이터 0선 하향 돌파: {previous_hist:.4f} → {current_hist:.4f}"
        else:
            reason = f"MACD 오실레이터 유지 중: {current_hist:.4f} (0선 돌파 없음)"

        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Sell Signal'] = sell_signal
                entry['Reason'] = reason           
            
        return buy_signal, sell_signal
    
    def stochastic_trading(self, df, symbol, k_threshold=20, d_threshold=80):
        """
        스토캐스틱 기반 매매 신호 생성
        - 기본 조건: 골든/데드 크로스 + 과매도/과매수 영역
        - 보완 조건: %K ≤ 30 골든크로스, %K ≥ 70 데드크로스
        - 신호 강도 구분: "normal" / "strong"
        """

        if df.shape[0] < 2:
            print("❌ 스토캐스틱 계산을 위한 데이터가 부족합니다.")
            return False, False

        df['%K'] = df['stochastic_k']
        df['%D'] = df['stochastic_d']

        candle = df.iloc[-1]
        trade_date = candle.name.date()
        close_price = float(candle['Close'])
        volume = candle['Volume']

        current_k = candle['%K']
        current_d = candle['%D']
        prev_k = df['%K'].iloc[-2]
        prev_d = df['%D'].iloc[-2]

        buy_signal = False
        sell_signal = False
        signal_strength = None
        reason = ""

        # ✅ 기본 매수 조건
        if (current_k > current_d) and (prev_k <= prev_d) and (current_k < k_threshold):
            buy_signal = True
            signal_strength = "normal"
            reason = (f"[기본 매수] 골든크로스: %K {prev_k:.2f} → {current_k:.2f}, "
                    f"%D {prev_d:.2f} → {current_d:.2f}, 과매도 영역 상승")

        # ✅ 기본 매도 조건
        
        elif (current_k < current_d) and (prev_k >= prev_d) and (current_k > d_threshold):
            sell_signal = True
            signal_strength = "normal"
            reason = (f"[기본 매도] 데드크로스: %K {prev_k:.2f} → {current_k:.2f}, "
                    f"%D {prev_d:.2f} → {current_d:.2f}, 과매수 영역 하락")

        # # ✅ 보완 매수 조건 (강한 신호)
        # if (current_k > current_d) and (prev_k <= prev_d) and (current_k <= 30):
        #     buy_signal = True
        #     signal_strength = "strong"
        #     reason = (f"[강한 매수] 30 이하 골든크로스: %K {prev_k:.2f} → {current_k:.2f}, "
        #             f"%D {prev_d:.2f} → {current_d:.2f}")

        # # ✅ 보완 매도 조건 (강한 신호)
        # elif (current_k < current_d) and (prev_k >= prev_d) and (current_k >= 70):
        #     sell_signal = True
        #     signal_strength = "strong"
        #     reason = (f"[강한 매도] 70 이상 데드크로스: %K {prev_k:.2f} → {current_k:.2f}, "
        #             f"%D {prev_d:.2f} → {current_d:.2f}")

        # ✅ 신호 없음
        else:
            reason = (f"%K {prev_k:.2f} → {current_k:.2f}, %D {prev_d:.2f} → {current_d:.2f}, "
                    f"스토캐스틱 조건 미충족")
            signal_strength = None

        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Sell Signal'] = sell_signal
                entry['Strength'] = signal_strength
                entry['Reason'] = reason

        return buy_signal, sell_signal
        
    def ema_breakout_trading(self, df, symbol):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록
        조건:
        ② 현재 시점: EMA_10이 EMA_50을 아래에서 위로 돌파
        ③ 현재 EMA_10, EMA_20, EMA_50의 기울기 ≥ 0
        ④ 거래량이 5일 평균 이상
        ⑤ 당일 윗꼬리 음봉이면 제외
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 ema_breakout_trading2 조건 계산 불가")
            return False, None

        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()
        last_close_price = float(last['Close'])
        prev_close_price = float(prev['Close'])

        # 조건 2: EMA_10이 EMA_50 상향 돌파
        cross_up = (
            prev['EMA_10'] < prev['EMA_50'] and
            last['EMA_10'] > last['EMA_50']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] / prev['Volume'] >= 1.5
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외
        is_bearish = last['Close'] < last['Open']
        # upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        # long_upper_shadow = is_bearish and upper_shadow_ratio > 0.4  # 윗꼬리 40% 이상이면 제외
        long_upper_shadow = is_bearish
        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up and not long_upper_shadow

        # 매매 사유 작성
        if buy_signal:
            reason = (
                f"매수 신호 발생: "
                f"[현재 EMA10 상향 돌파 EMA50] {prev['EMA_10']:.2f} → {last['EMA_10']:.2f} vs EMA50 {last['EMA_50']:.2f}, "
                f"[기울기] EMA10: {ema10_slope:.2f}, EMA20: {ema20_slope:.2f}, EMA50: {ema50_slope:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일평균 {last['Volume_MA5']:.0f}"
            )
        else:
            if long_upper_shadow:
                reason = "❌ 당일 윗꼬리 음봉 → 매수 조건 탈락"
            else:
                reason = "EMA 배열 돌파 조건 불충족"

        # trade_reasons에 결과 기록
        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Buy Reason'] = reason

        return buy_signal, None
    
    def bollinger_band_trading(self, lower_band, upper_band, df):
        """
        볼린저 밴드 기반 매매 신호 생성
        매수: 현재 종가가 하단 밴드보다 작거나 같음
        매도: 현재 종가가 상단 밴드보다 크거나 같음

        :param previous_closes: 과거 종가 리스트 (최소 20개 권장)
        :param current_close: 현재 종가
        :return: (buy_signal: bool, sell_signal: bool)
        """

        if lower_band == upper_band and df.shape[0] < 2:
            return False, False

        # EMA20 기울기(3일 차이)
        df['EMA60_slope'] = df['EMA_60'] - df['EMA_60'].shift(3)
        df['EMA20_slope'] = df['EMA_20'] - df['EMA_20'].shift(3)        
        # 조건 계산
        last = df.iloc[-1]
        prev = df.iloc[-2]        

        buy_signal = prev['Close'] < lower_band and last['Close'] > lower_band and (last['EMA60_slope'] > 0)  
        sell_signal = prev['Close'] > upper_band and last['Close'] < upper_band and (last['EMA60_slope'] < 0) 

        return buy_signal, sell_signal
    
    def ema_breakout_trading2(self, df, symbol):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록
        조건:
        ② 현재 시점: EMA_10이 EMA_50을 아래에서 위로 돌파
        ③ 현재 EMA_10, EMA_20, EMA_50의 기울기 ≥ 0
        ④ 거래량이 5일 평균 이상
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 ema_breakout_trading2 조건 계산 불가")
            return False, None

        # 5일 평균 거래량
        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()
        last_close_price = float(last['Close'])
        prev_close_price = float(prev['Close'])

        # 조건 2: EMA_10이 EMA_50 상향 돌파
        cross_up = (
            prev['EMA_10'] < prev['EMA_50'] and
            last['EMA_10'] > last['EMA_50']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        
        

        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up

        # 매매 사유 작성
        if buy_signal:
            reason = (
                f"매수 신호 발생: "
                f"[현재 EMA10 상향 돌파 EMA50] {prev['EMA_10']:.2f} → {last['EMA_10']:.2f} vs EMA50 {last['EMA_50']:.2f}, "
                f"[기울기] EMA10: {ema10_slope:.2f}, EMA20: {ema20_slope:.2f}, EMA50: {ema50_slope:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일평균 {last['Volume_MA5']:.0f}"
            )
        else:
            reason = "EMA 배열 돌파 조건 불충족"

        # trade_reasons에 결과 기록
        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Buy Reason'] = reason

        return buy_signal, None

    def trend_entry_trading(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록
        조건:
        ② 현재 시점: EMA_10이 EMA_50을 아래에서 위로 돌파
        ③ 현재 EMA_10, EMA_20, EMA_50의 기울기 ≥ 0
        ④ 거래량이 5일 평균 이상
        ⑤ 당일 윗꼬리 음봉이면 제외
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 ema_breakout_trading2 조건 계산 불가")
            return False, None

        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()
        
        close_price = float(last['Close'])
        volume = float(last['Volume'])

        # 조건 1: 거래대금 계산(30억 이상)
        trade_value = close_price * volume
    
        # 조건 2: EMA_10이 EMA_20 상향 돌파
        cross_up = (
            prev['EMA_10'] < prev['EMA_20'] and
            last['EMA_10'] > last['EMA_20']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외
        is_bearish = last['Close'] < last['Open']
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow  = upper_shadow_ratio <= 0.5  # 윗꼬리 50% 이상이면 제외
        long_upper_shadow = is_bearish
        
        # #✅ 조건 5: 고가 대비 종가 차이 10% 미만
        # high_close_diff_ratio = (last['High'] - last['Close']) / last['High']
        # not_big_gap_from_high = high_close_diff_ratio < 0.10
        
        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up and not long_upper_shadow and volume_up2 and not_long_upper_shadow

        # 매매 사유 작성
        if buy_signal:
            reason = (
                f"매수 신호 발생: "
                f"[현재 EMA10 상향 돌파 EMA50] {prev['EMA_10']:.2f} → {last['EMA_10']:.2f} vs EMA50 {last['EMA_50']:.2f}, "
                f"[기울기] EMA10: {ema10_slope:.2f}, EMA20: {ema20_slope:.2f}, EMA50: {ema50_slope:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일평균 {last['Volume_MA5']:.0f}"
            )
        else:
            if long_upper_shadow:
                reason = "❌ 당일 윗꼬리 음봉 → 매수 조건 탈락"
            else:
                reason = "EMA 배열 돌파 조건 불충족"

        return buy_signal, None
    
    def bottom_rebound_trading(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록
        조건:
        ② 현재 시점: EMA_10이 EMA_50을 아래에서 위로 돌파
        ③ 현재 EMA_10, EMA_20, EMA_50의 기울기 ≥ 0
        ④ 거래량이 5일 평균 이상
        ⑤ 당일 윗꼬리 음봉이면 제외
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 ema_breakout_trading2 조건 계산 불가")
            return False, None

        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()
        last_close_price = float(last['Close'])
        prev_close_price = float(prev['Close'])

        # 조건 2: EMA_10이 EMA_20 상향 돌파
        cross_up = (
            prev['EMA_10'] < prev['EMA_20'] and
            last['EMA_10'] > last['EMA_20']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']
        #volume_up2 = last['Volume'] / prev['Volume'] >= 1.5
        #거래대금은 아직..(코스닥은 20~30억, 코스피는 50억 이상 권장)
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외
        is_bearish = last['Close'] < last['Open']
        #is_bearish2 = prev['Close'] < prev['Open'] #전일 음봉 제외
        
        # upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        # long_upper_shadow = is_bearish and upper_shadow_ratio > 0.4  # 윗꼬리 40% 이상이면 제외
        long_upper_shadow = is_bearish
        
        # ✅ 조건 5: 고가 대비 종가 차이 10% 미만
        high_close_diff_ratio = (last['High'] - last['Close']) / last['High']
        not_big_gap_from_high = high_close_diff_ratio < 0.10
        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up and not long_upper_shadow and not_big_gap_from_high and volume_up2

        # 매매 사유 작성
        if buy_signal:
            reason = (
                f"매수 신호 발생: "
                f"[현재 EMA10 상향 돌파 EMA50] {prev['EMA_10']:.2f} → {last['EMA_10']:.2f} vs EMA50 {last['EMA_50']:.2f}, "
                f"[기울기] EMA10: {ema10_slope:.2f}, EMA20: {ema20_slope:.2f}, EMA50: {ema50_slope:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일평균 {last['Volume_MA5']:.0f}"
            )
        else:
            if long_upper_shadow:
                reason = "❌ 당일 윗꼬리 음봉 → 매수 조건 탈락"
            else:
                reason = "EMA 배열 돌파 조건 불충족"

        return buy_signal, None


    def downtrend_sell_trading(self, df):
        """
        df: DataFrame with columns ['Close', 'EMA_5', 'EMA_10', 'Low']
        """
        if len(df) < 3:
            return None, False  # 데이터 부족

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 조건 1: 5일 EMA 데드크로스
        dead_cross = prev['EMA_5'] > prev['EMA_10'] and last['EMA_5'] < last['EMA_10']
        
                # 조건 3: EMA 기울기 음수
        ema5_slope = last['EMA_5'] - prev['EMA_5']
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        
        slope_up = ema10_slope <= 0 and ema20_slope <= 0 and ema5_slope <= 0

        sell_signal = dead_cross and slope_up
        
        return None, sell_signal
    
    def top_reversal_sell_trading(self, df):
        """
        고점 반락형 매도 전략
        조건:
        ① 전날 RSI, MFI, Stoch > 임계값
        ② 오늘 RSI, MFI, Stoch 임계값 아래로 하락
        ③ MACD, 히스토그램 하락
        """
        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 조건 계산 불가")
            return None, False

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 조건 1: 전날 과매수
        prev_overbought = (
            prev['rsi'] >= 70 and
            prev['mfi'] >= 70 and
            prev['stochastic_k'] >= 80
        )

        # 조건 2: 오늘 하락 돌파
        breakdown_today = (
            last['rsi'] < 70 and
            last['mfi'] < 70 and
            last['stochastic_k'] < 80
        )

        # 조건 3: MACD 약화
        macd_falling = (
            last['macd'] < prev['macd'] and
            last['macd_histogram'] < prev['macd_histogram']
        )

        sell_signal = prev_overbought and breakdown_today and macd_falling

        return None, sell_signal
    
    def sma_breakout_trading(self, df, symbol):
        """
        ✅ 단순이동평균(SMA) 기반 매수 신호 로직
        조건:
        ① SMA_5가 SMA_40을 아래에서 위로 돌파
        ② SMA_5, SMA_20, SMA_40 기울기 ≥ 0
        ③ 현재 거래량이 5일 평균 이상
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 SMA 매수 조건 계산 불가")
            return False, None

        # 필수 컬럼 계산
        df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()

        # 조건 ①: SMA_5가 SMA_40을 아래에서 위로 돌파 (골든크로스)
        cross_up = prev['SMA_5'] < prev['SMA_40'] and last['SMA_5'] > last['SMA_40']

        # 조건 ②: SMA_5, SMA_20, SMA_40의 기울기 ≥ 0
        slope_5 = last['SMA_5'] - prev['SMA_5']
        slope_20 = last['SMA_20'] - prev['SMA_20']
        slope_40 = last['SMA_40'] - prev['SMA_40']
        slope_up = slope_5 >= 0 and slope_20 >= 0 and slope_40 >= 0

        # 조건 ③: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']

        # 최종 매수 조건
        buy_signal = cross_up and slope_up and volume_up

        # 매수 사유 설명
        if buy_signal:
            reason = (
                f"매수 신호 발생: SMA5→40 골든크로스, "
                f"기울기(10:{slope_5:.2f}, 20:{slope_20:.2f}, 40:{slope_40:.2f}), "
                f"거래량 {last['Volume']:.0f} > 평균 {last['Volume_MA5']:.0f}"
            )
        else:
            reason = "SMA 기반 조건 불충족"

        # 매매 사유 기록
        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Buy Reason'] = reason

        return buy_signal, None
    
    def ema_breakout_trading3(self, df, symbol):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록
        조건:
        ② 현재 시점: EMA_10이 EMA_50을 아래에서 위로 돌파
        ③ 현재 EMA_10, EMA_20, EMA_50의 기울기 ≥ 0
        ④ 거래량이 5일 평균 이상
        ⑤ 당일 윗꼬리 음봉이면 제외
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 ema_breakout_trading2 조건 계산 불가")
            return False, None

        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()
        last_close_price = float(last['Close'])
        prev_close_price = float(prev['Close'])

        # 조건 2: EMA_10이 EMA_50 상향 돌파
        cross_up = (
            prev['EMA_10'] < prev['EMA_50'] and
            last['EMA_10'] > last['EMA_50']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']

        # ❌ 조건 5: 당일 윗꼬리 음봉 제외
        is_bearish = last['Close'] < last['Open']
        # upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        # long_upper_shadow = is_bearish and upper_shadow_ratio > 0.4  # 윗꼬리 40% 이상이면 제외
        long_upper_shadow = is_bearish
        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up and not long_upper_shadow

        # 매매 사유 작성
        if buy_signal:
            reason = (
                f"매수 신호 발생: "
                f"[현재 EMA10 상향 돌파 EMA50] {prev['EMA_10']:.2f} → {last['EMA_10']:.2f} vs EMA50 {last['EMA_50']:.2f}, "
                f"[기울기] EMA10: {ema10_slope:.2f}, EMA20: {ema20_slope:.2f}, EMA50: {ema50_slope:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일평균 {last['Volume_MA5']:.0f}"
            )
        else:
            if long_upper_shadow:
                reason = "❌ 당일 윗꼬리 음봉 → 매수 조건 탈락"
            else:
                reason = "EMA 배열 돌파 조건 불충족"

        # trade_reasons에 결과 기록
        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                entry['Buy Signal'] = buy_signal
                entry['Buy Reason'] = reason

        return buy_signal, None
    
    def rsi_trading2(self, candle, rsi_values, symbol, buy_threshold= 30, sell_threshold= 70):
        """
        RSI를 기반으로 매수/매도 신호를 계산하는 함수.
        sell할 때 RSI 값을 돌파할 때로 설정
        """
        
        # ✅ None 값 제거 (dropna() 대신 직접 필터링)
        rsi_values = [rsi for rsi in rsi_values if rsi is not None]

        # ✅ NaN 제거 후 데이터 확인
        if len(rsi_values) < 2:
            return False, False  # 기본값 반환
        
        previous_rsi = rsi_values[-2]
        current_rsi = rsi_values[-1]
        
        # ✅ 기본값 설정
        buy_signal = False
        sell_signal = False
        reason = ""

        trade_date = candle.time.date()  # 날짜만 추출 (YYYY-MM-DD)
        close_price = float(candle.close)
        volume = candle.volume
        # 📌 매수 신호 판단 (Buy)
        if previous_rsi <= buy_threshold and current_rsi > buy_threshold:
            buy_signal = True
            reason = f"RSI {previous_rsi:.2f} → {current_rsi:.2f} (Buy Threshold {buy_threshold} 초과)"

        # 📌 매도 신호 판단 (Sell)
        elif previous_rsi < sell_threshold and current_rsi >= sell_threshold:
            sell_signal = True
            reason = f"RSI {previous_rsi:.2f} → {current_rsi:.2f} (Sell Threshold {sell_threshold} 하락)"

        # 📌 매수/매도 신호가 없는 경우, 이유 저장
        else:
            if previous_rsi > buy_threshold and current_rsi > buy_threshold:
                reason = ("RSI가 이미 매수 임계값 이상, 추가 매수 없음")
            elif previous_rsi < sell_threshold and current_rsi < sell_threshold:
                reason = ("RSI가 이미 매도 임계값 이하, 추가 매도 없음")
            elif previous_rsi > buy_threshold and current_rsi < buy_threshold:
                reason = ("RSI가 매수 임계값을 초과했으나 다시 하락")
            elif previous_rsi < sell_threshold and current_rsi > sell_threshold:
                reason = ("RSI가 매도 임계값 이하였으나 다시 상승")
            else:
                reason = ("RSI 기준 충족하지 않음")

        for entry in self.trade_reasons:
            if entry['Time'].date() == trade_date and entry['symbol'] == symbol:
                #entry['Buy Signal'] = buy_signal
                entry['Sell Signal'] = sell_signal
                entry['Reason'] = reason           
            
        return buy_signal, sell_signal
    
    def ema_crossover_trading(self, df, symbol):
        """
        📈 EMA 교차 기반 매수 조건
        조건:
        ① d-1일 10EMA < d-2일 10EMA
        ② d일 10EMA > d-1일 10EMA
        ③ d일 50EMA > d-1일 50EMA
        ④ d일 10EMA > d일 50EMA
        ⑤ d일 종가 > d일 10EMA
        ⑥ d일 종가 > d-1일 종가
        """
        if df.shape[0] < 3:
            print(f"❌ 데이터 부족으로 조건 계산 불가: {symbol}")
            return False, None

        d = df.iloc[-1]
        d_1 = df.iloc[-2]
        d_2 = df.iloc[-3]

        # 조건 계산
        cond_1 = d_1['EMA_10'] < d_2['EMA_10']
        cond_2 = d['EMA_10'] > d_1['EMA_10']
        cond_3 = d['EMA_50'] > d_1['EMA_50']
        cond_4 = d['EMA_10'] > d['EMA_50']
        cond_5 = d['Close'] > d['EMA_10']
        cond_6 = d['Close'] > d_1['Close']
        cond_7 = d['EMA_20'] > d_1['EMA_20']
        cond_8 = d_1['EMA_10'] < d_1['EMA_50']*(1+0.04)

        buy_signal = all([cond_1, cond_2, cond_3, cond_4, cond_5, cond_6, cond_7, cond_8])
        
        return buy_signal, None
    
    def should_sell(self, df):
        """
        df: DataFrame with columns ['Close', 'EMA_5', 'EMA_10', 'Low']
        """
        if len(df) < 3:
            return None, False  # 데이터 부족

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 조건 1: 5일 EMA 데드크로스
        dead_cross = prev['EMA_10'] > prev['EMA_20'] and last['EMA_10'] < last['EMA_20']
        
                # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        slope_up = ema10_slope <= 0 and ema20_slope <= 0 and ema50_slope <= 0

        sell_signal = dead_cross and slope_up
        
        return None, sell_signal
    
    def break_prev_low(self, df):
        """
        현재 종가가 전일 저가보다 낮아지면 매도 (지지선 이탈)
        
        df: DataFrame with columns ['Close', 'Low']
        """
        if len(df) < 2:
            return None, False  # 데이터 부족

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 전일 저가 이탈 여부
        sell_signal = last['Close'] < prev['Low']

        return None, sell_signal