from app.utils.technical_indicator import TechnicalIndicator
import pandas as pd
import io
import numpy as np


# 보조지표 클래스 선언
indicator = TechnicalIndicator()
class TradingLogic:

    def __init__(self):
        self.trade_reasons = []

### -------------------------------------------------------------매수로직-------------------------------------------------------------
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

        return buy_signal, None
    
    def ema_breakout_trading2(self, df, symbol):
        """
        황금비로 지수이동평균 계산

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
    
    def bottom_rebound_trading(self, df):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """
        buy_yn1, _ = self.trend_entry_trading(df)
        buy_yn2, _ = self.ema_crossover_trading(df)
        buy_yn3, _ = self.should_buy_break_high_trend(df)
    
        buy_signal = buy_yn1 and buy_yn2 and buy_yn3
        return buy_signal, None
    
    def sma_breakout_trading(self, df, symbol):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """
        buy_yn1, _ = self.weekly_trading(df)
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
    
    def ema_crossover_trading(self, df, last_resistance):
        if len(df) < 2:
            return False, None

        if last_resistance is None:
            return False, None
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev_prev = df.iloc[-3]
        # ✅ 중장기 정배열 조건
        long_trend = (
            last['EMA_10'] > last['EMA_20'] > last['EMA_60'] > last['EMA_120']
        )

        # ✅ EMA_5가 전일 EMA_13 아래에 있다가 당일 상향 돌파
        crossover = prev['Close'] <= prev['EMA_5'] and last['Close'] > last['EMA_5']

        # ✅ 종가가 EMA_5, EMA_13 위에 있어야 신뢰도 ↑
        price_above = last['Close'] > last['EMA_5'] and last['Close'] > last['EMA_10']

        # ✅ 거래량 조건 (5일 평균 이상 & 전일보다 증가)
        volume_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
        volume_good = last['Volume'] > volume_ma5 and last['Volume'] > prev['Volume']

        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        cond5  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
        cond6 = last['Close'] > last["Open"]
        
        cond7 = prev_prev['Close'] >= prev_prev['EMA_5'] and prev['Close'] <= prev['EMA_5'] and last['Close'] > last['EMA_5']
        
                # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_5'] - prev['EMA_5']
        ema60_slope = last['EMA_60'] - prev['EMA_60']
        
        slope_up = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0 and ema60_slope > 0
        
        # 고점 돌파 (최근 5일 고점)
        recent_close_high = df['High'].iloc[-6:-1].max()
        cond8 = last['Close'] > recent_close_high
        
        cond9 = last['Close'] > last_resistance
        # ✅ 최종 매수 조건
        buy_signal = all([long_trend, crossover, not cond7, cond6, slope_up, volume_good, cond5, cond9])
        
        return buy_signal, None
    
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
        ema50_slope = last['EMA_60'] - prev['EMA_60']
        ema120_slope = last['EMA_120'] - prev['EMA_120']
        cond10 = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0 and ema120_slope > 0
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        cond11  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
        
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
    
        buy_signal = all([cond7, cond6, cond9, cond3, cond11, cond10])
        
        return buy_signal, None

    def trendline_breakout_trading(self, df, resistance):
        """
        매수 조건:
        - 고점 수평선(horizontal_high)을 돌파
        - 현재 종가(price)가 EMA_5 위에 위치
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
    
    def should_buy_break_high_trend(self, df):
        if len(df) < 90:
            return False, None
    
        if 'Volume_MA5' not in df.columns:
            df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 고점 돌파 (최근 20일 고점)
        recent_high = df['High'].iloc[-21:-1].max()
        cond1 = last['Close'] > recent_high

        cond2 = prev['Close'] < prev['EMA_120']
        # 종가 > EMA_5 (단기 강세)
        cond3 = last['Close'] > last['EMA_120'] and last['Close'] > last['EMA_60']
        

        # 이전 봉보다 거래량 증가 (수급 강화)
        cond4 = last['Volume'] > prev['Volume'] and last['Volume_MA5'] < last['Volume']
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        cond5  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
        
                # 조건 3: EMA 기울기 양수
        ema10_slope = last['EMA_10'] - prev['EMA_10']
        ema20_slope = last['EMA_20'] - prev['EMA_20']
        ema50_slope = last['EMA_5'] - prev['EMA_5']
        ema60_slope = last['EMA_60'] - prev['EMA_60']
        
        cond6 = ema10_slope > 0 and ema20_slope > 0 and ema50_slope > 0 and ema60_slope > 0

        buy_signal = all([cond1, cond2, cond3, cond5, cond4, cond6])

        return buy_signal, None

    
    def weekly_trading(self, df, last_resistance):
        """
        EMA 배열 + 상향 돌파 기반 매수 신호 생성 및 사유 기록

        """

        if df.shape[0] < 2:
            print("❌ 데이터가 부족해서 trend_entry_trading 조건 계산 불가")
            return False, None

        if last_resistance is None:
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
        is_bearish = last['Close'] > last['Open'] and prev['Close'] > prev['Open']
        
        upper_shadow_ratio = (last['High'] - max(last['Open'], last['Close'])) / (last['High'] - last['Low'] + 1e-6)
        not_long_upper_shadow  = upper_shadow_ratio <= 0.8  # 윗꼬리 80% 이상이면 제외
        
        # 고점 돌파 (최근 20일 고점)
        recent_high = df['High'].iloc[-16:-1].max()
        cond15 = last['Close'] > recent_high
        print(f"last_resistance: {last_resistance}")
        cond16 = last['Close'] > last_resistance
        # 최종 조건
        buy_signal = all([cross_up, slope_up, is_bearish, not_long_upper_shadow, volume_up , volume_up2, cond16 ])

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
    
    
    
    


### -------------------------------------------------------------매도로직-------------------------------------------------------------

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

        return None, sell_signal
    
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
        ema50_slope = last['EMA_55'] - prev['EMA_55']
        slope_up = ema10_slope <= 0 and ema20_slope <= 0 and ema50_slope <= 0

        sell_signal = dead_cross and slope_up
        
        return None, sell_signal
    
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
        dead_cross = last['EMA_5'] < last['EMA_10'] and last['EMA_5'] > last['Close']

        sell_signal = dead_cross
        
        return None, sell_signal