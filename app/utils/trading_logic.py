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
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록 + 볼린저밴드 돌파 조건 추가
        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 ema_breakout_trading 조건 계산 불가")
            return False, None

        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()

        close_price = float(last['Close'])
        volume = float(last['Volume'])

        # 조건 1: EMA 상향 돌파
        cross_up = (
            prev['EMA_10'] < prev['EMA_20'] and
            last['EMA_10'] > last['EMA_20']
        )

        # 조건 2: EMA 기울기
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_55'] - prev['EMA_55']
        ema60_slope = last['EMA_60'] - prev['EMA_60']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0 and ema60_slope > 0 

        # 조건 3: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']

        # 조건 4: 윗꼬리 음봉 제외
        is_bearish = last['Close'] < last['Open']
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow = upper_shadow_ratio <= 0.8 #50% 이하만 매수
        long_upper_shadow = is_bearish

        # 조건 5: 전일 종가 대비 20% 이상 상승 제외
        # price_increase_ratio = (close_price - float(prev['Close'])) / float(prev['Close'])
        # price_up_limit = price_increase_ratio < 0.2

        # #✅ 조건 6: 고가 대비 종가 차이 5% 미만
        # close_near_high = last['Close'] >= last['High'] * 0.95
        
        # ✅ 조건 7: 볼린저밴드 돌파 조건 (중단선 or 상단선 돌파만 허용)
        if prev['Close'] < prev['BB_Middle']:
            valid_bollinger_breakout = last['Close'] > last['BB_Middle']
        elif prev['Close'] < prev['BB_Upper']:
            valid_bollinger_breakout = last['Close'] > last['BB_Upper']
        else:
            valid_bollinger_breakout = True

        # ✅ 조건 7: 몸통 비율 ≥ 30%
        # body_length = abs(last['Close'] - last['Open'])
        # candle_range = last['High'] - last['Low'] + 1e-6
        # body_ratio = body_length / candle_range
        # body_sufficient = body_ratio >= 0.3
    
        # ✅ 최종 조건
        buy_signal = (
            cross_up and slope_up and volume_up and volume_up2 and
            not long_upper_shadow and not_long_upper_shadow and
            valid_bollinger_breakout
        )

        # 📌 매매 사유 작성
        if buy_signal:
            reason = (
                f"매수 신호 발생: EMA 배열 상향 돌파 + 볼린저밴드 유효 돌파 "
                f"[EMA10 상향 돌파 EMA50] {prev['EMA_10']:.2f} → {last['EMA_10']:.2f}, "
                f"[기울기] EMA10: {ema10_slope:.2f}, EMA20: {ema20_slope:.2f}, EMA50: {ema50_slope:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일평균 {last['Volume_MA5']:.0f}"
            )
        else:
            if long_upper_shadow:
                reason = "❌ 당일 윗꼬리 음봉 → 매수 조건 탈락"
            elif not valid_bollinger_breakout:
                reason = "❌ 볼린저밴드 돌파 조건 불충족"
            else:
                reason = "❌ EMA 배열 돌파 조건 불충족"

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

        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 trend_entry_trading 조건 계산 불가")
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
            prev['EMA_13'] <= prev['EMA_21'] and
            last['EMA_13'] > last['EMA_21']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_13'] - prev['EMA_13']
        ema20_slope = last['EMA_21'] - prev['EMA_21']
        ema50_slope = last['EMA_55'] - prev['EMA_55']
        ema60_slope = last['EMA_89'] - prev['EMA_89']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외, 윗꼬리 조건 추가
        is_bearish = last['Close'] > last['Open']
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
    
        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up and is_bearish and volume_up2 and not_long_upper_shadow

        return buy_signal, None

    def trend_entry_trading(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 trend_entry_trading 조건 계산 불가")
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
            prev['EMA_10'] <= prev['EMA_20'] and
            last['EMA_10'] > last['EMA_20']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_5'] - prev['EMA_5']
        ema20_slope = last['EMA_10'] - prev['EMA_10']
        ema50_slope = last['EMA_20'] - prev['EMA_20']
        ema60_slope = last['EMA_60'] - prev['EMA_60']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0 and ema60_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외, 윗꼬리 조건 추가
        is_bearish = last['Close'] > last['Open']
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
    
        # 최종 조건
        buy_signal = cross_up and slope_up and volume_up and is_bearish and volume_up2 and not_long_upper_shadow

        return buy_signal, None
    
    def bottom_rebound_trading(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """

        if df.shape[0] < 11:
            print("❌ 데이터가 부족해서 trend_entry_trading 조건 계산 불가")
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

        # ✅ 1. 과거 정배열이 꾸준히 유지되었는가? (10~5일 전까지)
        ordered_history = []
        for i in range(-5, -2):  # D-10 ~ D-6 (정배열 유지 확인)
            e5 = df['EMA_5'].iloc[i]
            e13 = df['EMA_13'].iloc[i]
            e21 = df['EMA_21'].iloc[i]
            e55 = df['EMA_55'].iloc[i]
            ordered_history.append(e55 > e21 > e13 > e5)
        was_strictly_ordered = all(ordered_history)

        # ✅ 2. 최근 5일 동안 정배열이 깨졌는가? (하나라도 깨지면 True)
        broken_recently = False
        for i in range(-5, 0):
            e5 = df['EMA_5'].iloc[i]
            e13 = df['EMA_13'].iloc[i]
            e21 = df['EMA_21'].iloc[i]
            e55 = df['EMA_55'].iloc[i]
            if not (e55 > e21 > e13 > e5):
                broken_recently = True
                break
        
        # ✅ 3. 오늘 종가가 EMA_55를 상향 돌파했는가?
        crossed_ema55_today = (
            prev['Close'] <= prev['EMA_55'] and
            last['Close'] > last['EMA_55'] and
            last['Close'] > last['EMA_89']
        )

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_13'] - prev['EMA_13']
        ema20_slope = last['EMA_21'] - prev['EMA_21']
        ema50_slope = last['EMA_55'] - prev['EMA_55']
        #ema60_slope = last['EMA_60'] - prev['EMA_60']
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외, 윗꼬리 조건 추가
        is_bullish = last['Close'] > last['Open']
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
        
            # ✅ 추가 조건: EMA60이 모든 단기선보다 위 + 종가가 EMA60 상향 돌파
        ema55_above_all = (
            last['EMA_5'] > last['EMA_13'] 

        )
        
        slope_ma_up = (
            last['EMA_55_Slope_MA'] > 0
        )
        
    # ✅ 최종 조건
        buy_signal = (
            crossed_ema55_today and
            slope_up and
            volume_up and volume_up2 and
            is_bullish and not_long_upper_shadow and
            slope_ma_up and ema55_above_all
        )

        return buy_signal, None

    def downtrend_sell_trading(self, df):
        """
        윗꼬리 긴 음봉일 때 매도 신호 발생
        """
        if len(df) < 3:
            return None, False  # 데이터 부족

        last = df.iloc[-1]
        
        open_price = last['Open']
        close_price = last['Close']
        high = last['High']
        low = last['Low']

        # 조건 2: 윗꼬리 비율이 50% 이상
        upper_shadow = high - max(open_price, close_price)
        body = abs(close_price - open_price)                # 몸통 길이
        total_range = high - low                # 전체 봉의 길이
        
        # 최종 조건
        sell_signal = upper_shadow >= body

        return None, sell_signal
    
    def top_reversal_sell_trading(self, df):
        """
        5일선이 10일 선 밑으로 갈 때
        """
        if len(df) < 3:
            return None, False  # 데이터 부족

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 조건 1: 5일 EMA 데드크로스
        dead_cross = prev['EMA_5'] >= prev['EMA_10'] and last['EMA_5'] < last['EMA_10']
        
                # 조건 3: EMA 기울기 음수
        ema10_slope = last['EMA_5'] - prev['EMA_5']
        ema20_slope = last['EMA_10'] - prev['EMA_10']
        slope_up = ema10_slope <= 0 and ema20_slope <= 0 

        sell_signal = dead_cross and slope_up
        
        return None, sell_signal
    
    def sma_breakout_trading(self, df, symbol):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """
        buy_yn1, _ = self.anti_retail_ema_entry(df)
        buy_yn2, _ = self.ema_crossover_trading(df)
    
        buy_signal = buy_yn1 or buy_yn2
        return buy_signal, None
    
    def ema_breakout_trading3(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 trend_entry_trading 조건 계산 불가")
            return False, None
        
        # if high_trendline is None:
        #     return False, None

        df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
            
        # # 🔧 EMA 기울기 추가 및 이동평균 계산
        # df['EMA_50_Slope'] = df['EMA_50'] - df['EMA_50'].shift(1)
        # df['EMA_60_Slope'] = df['EMA_60'] - df['EMA_60'].shift(1)

        # df['EMA_50_Slope_MA'] = df['EMA_50_Slope'].rolling(window=3).mean()
        # df['EMA_60_Slope_MA'] = df['EMA_60_Slope'].rolling(window=3).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        trade_date = last.name.date()
        
        close_price = float(last['Close'])
        volume = float(last['Volume'])

        # 조건 1: 거래대금 계산(30억 이상)
        trade_value = close_price * volume

        # 조건 2: EMA_5이 EMA_20 상향 돌파
        cross_up = (
            prev['EMA_13'] < prev['EMA_21'] and
            last['EMA_13'] > last['EMA_21'] and
            last['EMA_5'] > last['EMA_13'] > last['EMA_21']
        )

        
        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_13'] - prev['EMA_13']
        ema20_slope = last['EMA_21'] - prev['EMA_21']
        ema50_slope = last['EMA_55'] - prev['EMA_55']
        ema60_slope = last['EMA_89'] - prev['EMA_89']
        
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0
        
            # ✅ 조건 3-1: EMA_50, EMA_60 기울기 평균도 양수여야 함
        slope_ma_up = (
            last['EMA_55_Slope_MA'] > 0
            and last['EMA_89_Slope_MA'] > 0
        )

        # 조건 4: 거래량 증가
        volume_up = last['Volume'] > last['Volume_MA5']
        volume_up2 = last['Volume'] > prev['Volume']
        
        # ❌ 조건 5: 당일 윗꼬리 음봉 제외, 윗꼬리 조건 강화
        is_bearish = last['Close'] < last['Open']
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow  = upper_shadow_ratio <= 0.8  # 윗꼬리 20% 이상이면 제외
        
        #조건 6
        prev_high_up = last['Close'] >= prev['High']
        
        
        # ✅ 조건 7: 최근 20일 내 고점 돌파
        recent_20_high = df['High'].iloc[-20:].max()
        close_breaks_recent_high = last['Close'] > recent_20_high
        


        # cond1 = prev['Close'] < high_trendline  # 하락추세선 아래 → 상향 돌파
        # cond2 = last['Close'] > high_trendline
        # cond3 = last['Close'] > last_resistance  # 수평 고점도 돌파
        
        
        # 최종 조건
        #buy_signal = cross_up and slope_up and not_long_upper_shadow and slope_ma_up and not is_bearish and volume_up and prev_high_up
        buy_signal = all([cross_up, slope_up, not_long_upper_shadow, slope_ma_up, not is_bearish, volume_up, prev_high_up]) 
        
        print(f"EMA_55_Slope_MA: {last['EMA_55_Slope_MA']}")
        print(f"EMA_89_Slope_MA: {last['EMA_89_Slope_MA']}")

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
    
    def ema_crossover_trading(self, df):
        if len(df) < 90:
            return False, None

        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev_prev = df.iloc[-3]
        # ✅ 중장기 정배열 조건
        long_trend = (
            last['EMA_10'] > last['EMA_20'] > last['EMA_60'] > last['EMA_120']
        )

        # ✅ EMA_5가 전일 EMA_13 아래에 있다가 당일 상향 돌파
        crossover = prev['EMA_5'] <= prev['EMA_10'] and last['EMA_5'] > last['EMA_10']

        # ✅ 종가가 EMA_5, EMA_13 위에 있어야 신뢰도 ↑
        price_above = last['Close'] > last['EMA_5'] and last['Close'] > last['EMA_10']

        # ✅ 거래량 조건 (5일 평균 이상 & 전일보다 증가)
        volume_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
        volume_good = last['Volume'] > volume_ma5 and last['Volume'] > prev['Volume']

        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        cond5  = upper_shadow_ratio <= 0.45  # 윗꼬리 80% 이상이면 제외
        cond6 = last['Close'] > last["Open"]
        
        cond7 = prev_prev['EMA_5'] >= prev_prev['EMA_10'] and prev['EMA_5'] <= prev['EMA_10'] and last['EMA_5'] > last['EMA_10']
        # ✅ 최종 매수 조건
        buy_signal = all([long_trend, crossover, not cond7])
        
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
        볼린저밴드 기반 매도 신호
        전일 종가의 위치에 따라 상단, 중단, 하단 이탈 여부를 판단

        df: DataFrame with columns ['Close', 'BB_Upper', 'BB_Middle', 'BB_Lower']
        return: reason(str or None), sell_signal (bool)
        """
        if len(df) < 3:
            return None, False  # 데이터 부족

        last = df.iloc[-1]
        prev = df.iloc[-2]

        reason = None
        sell_signal = False

        # ✅ 조건 1: 상단선 돌파 후 하향 이탈
        if prev['Close'] > prev['BB_Upper'] and last['Close'] < last['BB_Upper']:
            reason = (
                f"📉 상단 돌파 후 하락 → 매도: "
                f"전날 {prev['Close']:.2f} > 상단 {prev['BB_Upper']:.2f}, "
                f"오늘 {last['Close']:.2f} < 상단 {last['BB_Upper']:.2f}"
            )
            sell_signal = True

        # ✅ 조건 2: 중단~상단 사이 → 중단 이탈
        elif (
            prev['Close'] < prev['BB_Upper'] and
            prev['Close'] > prev['BB_Middle'] and
            last['Close'] < last['BB_Middle']
        ):
            reason = (
                f"📉 중단선 하향 이탈 → 매도: "
                f"전날 {prev['Close']:.2f} ∈ ({prev['BB_Middle']:.2f}, {prev['BB_Upper']:.2f}), "
                f"오늘 {last['Close']:.2f} < 중단 {last['BB_Middle']:.2f}"
            )
            sell_signal = True

        # ✅ 조건 3: 하단 이탈
        elif (
            prev['Close'] < prev['BB_Middle'] and
            prev['Close'] > prev['BB_Lower'] and
            last['Close'] < last['BB_Lower']
        ):
            reason = (
                f"📉 하단선 하향 이탈 → 매도: "
                f"전날 {prev['Close']:.2f} ∈ ({prev['BB_Lower']:.2f}, {prev['BB_Middle']:.2f}), "
                f"오늘 {last['Close']:.2f} < 하단 {last['BB_Lower']:.2f}"
            )
            sell_signal = True

        return None, sell_signal
    
    def sell_on_support_break(self, df):
        """
        2차 지지선 이탈 + 거래량 실린 음봉 조건의 매도 시그널
        - s2_level: 피봇 지표 등으로 계산된 2차 지지선 값 (float)
        """
        if df.shape[0] < 2:
            print("❌ 캔들 데이터 부족")
            return False, None

        # ✅ 전일 고가, 저가, 종가로 Pivot, S2 계산
        prev = df.iloc[-2]
        prev_high = prev['High']
        prev_low = prev['Low']
        prev_close = prev['Close']
        P = (prev_high + prev_low + prev_close) / 3
        s2_level = P - (prev_high - prev_low)
    
        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        
        # ✅ 조건 1: 2차 지지선 하회
        below_s2 = last['Close'] < s2_level

        # ✅ 조건 2: 음봉
        is_bearish_candle = last['Close'] < last['Open']

        # ✅ 조건 3: 거래량이 5일 평균 이상
        volume_heavy = last['Volume'] > prev['Volume']

        # ✅ 매도 시그널
        sell_signal = below_s2 and is_bearish_candle and volume_heavy

        # 🔎 사유 작성
        if sell_signal:
            reason = (
                f"매도 신호 발생: "
                f"[2차 지지선 이탈] Close {last['Close']:.2f} < S2 {s2_level:.2f}, "
                f"[음봉] Open {last['Open']:.2f} > Close {last['Close']:.2f}, "
                f"[거래량] {last['Volume']:.0f} > 5일 평균 {last['Volume_MA5']:.0f}"
            )
        else:
            reason = "조건 미충족"

        return None, sell_signal
    
    def anti_retail_ema_entry(self, df):
        """
        매수 조건:
        - 고점 수평선(horizontal_high)을 돌파
        - 현재 종가(price)가 EMA_5 위에 위치

        Parameters:
        - df: 반드시 'price', 'horizontal_high', 'EMA_5' 컬럼 포함 (최신 데이터가 마지막 row)

        Returns:
        - (bool, str): (매수 여부, 매수 사유)
        """
        if len(df) < 3:
            return False, None  # 데이터 부족

        # if resistance is None:
        #     return False, None
        if 'volume_MA5' not in df.columns:
            df['volume_MA5'] = df['Volume'].rolling(window=5).mean()
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev_prev = df.iloc[-3]
            
        # cond1 = last["Close"] > resistance >= prev['Close']
        cond1 = prev["Close"] >= prev["Open"]
        cond2 = last["Close"] > last["EMA_5"]
        cond3 = last['Close'] > last['Open']
        cond4 = prev['Volume'] > prev_prev['Volume']
        cond5 = last["EMA_55_Slope_MA"] > 0.4
        cond7 = last['EMA_10'] > last['EMA_20'] and prev['EMA_10'] <= prev['EMA_20']
                # 📌 정배열 조건
                
        # if prev["Close"] < prev["EMA_89"]:
        #     cond6 = last["Close"] >= last["EMA_89"]
        # else:
        #     cond6 = True
        
        cond6 = prev["Close"] <= prev["EMA_60"] and last["Close"] > last["EMA_60"]
                # ✅ EMA 배열이 역배열일 경우 매수 제외 (EMA_89 > EMA_55 > EMA_5 > EMA_13 > EMA_21)
        is_bad_arrangement = (
            last["EMA_60"] > last["EMA_50"] > last['EMA_5'] >  last["EMA_10"] > last["EMA_20"]
        )
        cond8 = not is_bad_arrangement
        
        cond9 = last['EMA_120'] > last["EMA_60"] > last["EMA_10"] > last["EMA_20"]
        #cond9 = last['EMA_89'] > last["EMA_55"] > last['EMA_5'] > last["EMA_13"] > last["EMA_21"]        
                # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_50'] - prev['EMA_50']
        ema60_slope = last['EMA_60'] - prev['EMA_60']
        cond10 = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        cond11  = upper_shadow_ratio <= 0.45  # 윗꼬리 80% 이상이면 제외
        
        cond12 = last["EMA_55_Slope_MA"] > 0.03 and last["EMA_89_Slope_MA"] > -0.02
        
        under_period = df.iloc[-31:-1]  # 전날까지 15일
        cond13 = all(under_period["EMA_13"] < under_period["EMA_21"])
        cond14 = last['Volume'] > last['volume_MA5'] and last['Volume'] > prev['Volume']
        
        # 고점 돌파 (최근 20일 고점)
        recent_high = df['High'].iloc[-26:-1].max()
        cond15 = last['Close'] > recent_high > prev['Close']
        
        cond16 = last['EMA_21'] > last['EMA_55'] and prev['EMA_21'] <= prev['EMA_55']
        cond17 = cond16 or cond7
        
            # ✅ 정배열 조건 확인
        is_bullish = (
            last['EMA_13'] > last['EMA_21'] > last['EMA_55'] > last['EMA_89']
        )

        if is_bullish:
            # 🔍 EMA_5가 EMA_13을 상향 돌파하는 순간
            crossed_up = prev['EMA_5'] <= prev['EMA_13'] and last['EMA_5'] > last['EMA_13']
        else:
            crossed_up = True
    
        buy_signal = all([cond7, cond6, cond9])
        
        return buy_signal, None

    def trendline_breakout_trading(self, df, resistance):
        """
        매수 조건:
        - 고점 수평선(horizontal_high)을 돌파
        - 현재 종가(price)가 EMA_5 위에 위치

        Parameters:
        - df: 반드시 'price', 'horizontal_high', 'EMA_5' 컬럼 포함 (최신 데이터가 마지막 row)

        Returns:
        - (bool, str): (매수 여부, 매수 사유)
        """
        if len(df) < 2:
            return False, None  # 데이터 부족

        if resistance is None:
            return False, None
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev_prev = df.iloc[-3]

        cond1 = last["Close"] > resistance >= prev['Close']
        cond2 = last["Close"] > last["EMA_5"]
        cond3 = last['Close'] > last['Open']
        cond4 = prev['Volume'] > prev_prev['Volume']
        cond5 = last["EMA_55_Slope_MA"] > 0.4
                # 📌 정배열 조건
        if last["Close"] > last["EMA_55"]:
            cond6 = last["EMA_5"] > last["EMA_13"] > last["EMA_21"] > last['EMA_89']
        else:
            cond6 = True  # 종가가 EMA_55 아래에 있으면 정배열 조건은 적용하지 않음
            
        cond7 =  (prev['EMA_13'] <= prev['EMA_21'] and
        last['EMA_13'] > last['EMA_21'])
    
        buy_signal = all([cond1, cond3, cond5,cond6, cond7])
        
        return buy_signal, None
    
    def should_buy(self, df, high_trendline, last_resistance):
        """
        - 하락 고점 추세선을 상향 돌파 + 최근 수평 고점도 돌파
        """
        if len(df) < 10 or 'horizontal_high' not in df.columns:
            return False, None

        #current_idx = len(df) - 1
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 고점 추세선 연장값
        
        if high_trendline is None:
            return False, None

        # # 가장 최근의 수평 고점
        # confirmed_highs = df.iloc[:current_idx - 5][df['horizontal_high'].notna()]
        # if confirmed_highs.empty:
        #     return False, None
        # last_resistance = confirmed_highs['horizontal_high'].iloc[-1]
        print(f"high_trendline: {high_trendline}")

        # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_55'] - prev['EMA_55']
        ema60_slope = last['EMA_60'] - prev['EMA_60']
        
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0 and ema60_slope > 0
        slope_up2 = last['EMA_5'] - prev['EMA_5']
        
            # ✅ 조건 3-1: EMA_50, EMA_60 기울기 평균도 양수여야 함
        slope_ma_up = (
            last['EMA_55_Slope_MA'] > 0
            and last['EMA_60_Slope_MA'] > 0
        )
        
        # 조건
        cond1 = prev['Close'] <= high_trendline  # 하락추세선 아래 → 상향 돌파
        cond2 = last['Close'] > high_trendline
        cond3 = last['Close'] >= last_resistance  # 수평 고점도 돌파
        cond4 = last['Close'] > last['Open']     # 양봉
        cond5 = last['Volume'] > prev['Volume']
        buy_signal = all([cond1, cond2, cond4, cond5, slope_up2])
        
        return buy_signal, None


    def horizontal_low_sell(self, df):
        """
        조건: 이전 종가 >= 수평 고점, 현재 종가 < 수평 고점 → 저항 실패
        """
        if len(df) < 3 or 'horizontal_low' not in df.columns:
            return None, False

        last = df.iloc[-1]
        prev = df.iloc[-2]

        resistance_row = df[df['horizontal_low'].notna()].iloc[-1:]
        if resistance_row.empty:
            return None, False

        support = resistance_row['horizontal_low'].values[0]

        sell_signal = prev['Close'] >= support > last['Close']

        return None, sell_signal
    
    def should_buy_break_high_trend(self, df, high_trendline, last_resistance):
        if len(df) < 90:
            return False, None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 고점 돌파 (최근 20일 고점)
        recent_high = df['High'].iloc[-26:-1].max()
        cond1 = last['Close'] > recent_high > prev['Close']

        # EMA 정배열 조건
        cond2 = (
            last['EMA_5'] > last['EMA_13'] >
            last['EMA_21'] > last['EMA_55'] > last['EMA_89']
        )

        # 종가 > EMA_5 (단기 강세)
        cond3 = last['Close'] > last['EMA_5'] and last['Close'] > last['EMA_13']

        # 이전 봉보다 거래량 증가 (수급 강화)
        cond4 = last['Volume'] > prev['Volume']
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        cond5  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외

        buy_signal = all([cond1, cond2, cond3, cond5])

        return buy_signal, None


    def should_sell_break_low_trend(self, df, window=5):
        """
        최근 저점들로 만든 추세선 이탈 시 매도
        """
        if len(df) < window + 1:
            return False, None

        lows = df['Low'].iloc[-window - 1:-1].values
        x = np.arange(len(lows))
        trendline_price = self.fit_trendline(x, lows)

        close_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]

        # 이전엔 추세선 위, 지금은 이탈
        if prev_close >= trendline_price and close_price < trendline_price:
            return True, f"📉 저점 추세선 이탈 매도 (기준가: {trendline_price:.2f})"

        return False, None
    
    def weekly_trading(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록
        
        """
        
        if len(df) < 2:
            return False, None  # 데이터 부족
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev_prev = df.iloc[-3]

        cond7 = last['EMA_10'] > last['EMA_20'] and prev['EMA_10'] <= prev['EMA_20']
        
        cond6 = prev["Close"] <= prev["EMA_60"] and last["Close"] > last["EMA_60"]
                # ✅ EMA 배열이 역배열일 경우 매수 제외 (EMA_89 > EMA_55 > EMA_5 > EMA_13 > EMA_21)
        is_bad_arrangement = (
            last["EMA_60"] > last["EMA_50"] > last['EMA_5'] >  last["EMA_10"] > last["EMA_20"]
        )
        cond8 = not is_bad_arrangement
        
        cond9 = last['EMA_120'] > last["EMA_60"] > last["EMA_10"] > last["EMA_20"]
        
        cond10 = last['Close'] > last['Open']
        print(f"{last['Close']}, {last['Open']}")
    
        # 최종 조건
        buy_signal = cond10

        return buy_signal, None

