import numpy as np
import pandas as pd


class TechnicalIndicator:
    
    # 볼린저밴드 계산
    def cal_bollinger_band(self, previous_closes, close_price):
    
        if len(previous_closes) >= 20:
            sma = np.mean(previous_closes[-20:])
            std = np.std(previous_closes[-20:])
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
        else:
            sma = np.mean(previous_closes) if previous_closes else close_price
            std = np.std(previous_closes) if len(previous_closes) > 1 else 0
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)

        band = {}
        band['upper'] = upper_band
        band['middle'] = sma
        band['lower'] = lower_band

        return band
    
    # 이동평균 계산
    def cal_ma(self, close_prices, window):
        # 마지막 3일 이동평균 계산
        if len(close_prices) >= window:
            sma_last = sum(close_prices[-window:]) / window
        else:
            sma_last = None  # 데이터가 부족할 경우 None
        
        return sma_last
    
    def cal_mfi_df(self, df, period=14):
        """
        ✅ MFI (Money Flow Index) 계산
        - MFI = 100 - (100 / (1 + Money Flow Ratio))
        
        테스트 결과 값이 정확히 계산됨
        """
        # ✅ Typical Price (TP) 계산
        df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3

        # ✅ Raw Money Flow (RMF) 계산
        df['RMF'] = df['TP'] * df['Volume']

        # ✅ 이전 TP 값 추가 (shift(1) 오류 방지)
        df['Prev_TP'] = df['TP'].shift(1)
        
        # ✅ Money Flow 비교 (TP가 상승/하락한 경우)
        df['Positive_MF'] = df.apply(lambda x: x['RMF'] if x['TP'] > x['Prev_TP'] else 0, axis=1)
        df['Negative_MF'] = df.apply(lambda x: x['RMF'] if x['TP'] < x['Prev_TP'] else 0, axis=1)

        # ✅ MFR (Money Flow Ratio) 계산
        df['PMF'] = df['Positive_MF'].rolling(window=period).sum()
        df['NMF'] = df['Negative_MF'].rolling(window=period).sum()
        df['MFR'] = df['PMF'] / (df['NMF'] + 1e-10)  # 0으로 나누는 문제 방지

        # ✅ MFI (Money Flow Index) 계산
        df['mfi'] = (100 - (100 / (1 + df['MFR']))).round(2)
        
        # 📌 처음 14일 동안의 데이터 제거 (이상값 방지)
        df.iloc[:period, df.columns.get_loc('mfi')] = np.nan
        
        return df

    def cal_rsi_df(self, df, period=14):
        """
        delta = 오늘 종가 - 어제 종가

        gain = 양의 delta (음수는 0으로)

        loss = 음의 delta의 절댓값 (양수는 0으로)

        avg_gain = 14일간 평균 gain

        avg_loss = 14일간 평균 loss

        RS = avg_gain / avg_loss

        RSI = 100 - (100 / (1 + RS)
        테스트 결과 값이 정확히 계산됨
        """
        
        delta = df['Close'].diff(1)  # 종가 변화량
        gain = delta.where(delta > 0, 0)  # 상승한 부분만 남기기
        loss = -delta.where(delta < 0, 0)  # 하락한 부분만 남기기
        
        # 📌 NaN 방지 & 초기값 설정 (최소 14개 이상 데이터 필요)
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        # 📌 0으로 나누는 문제 방지 (loss가 0일 때 예외 처리)
        rs = avg_gain / (avg_loss + 1e-10)  # 1e-10을 추가해서 0으로 나누는 것 방지
        df['rsi'] = (100 - (100 / (1 + rs))).round(2)  # RSI 계산
        
        # 📌 처음 14일 동안의 데이터 제거 (이상값 방지)
        df.iloc[:period, df.columns.get_loc('rsi')] = np.nan

        return df
    

    def cal_macd_df(self, df, short_window=12, long_window=26, signal_window=9):
        """
        MACD 오실레이터
        •	MACD (Moving Average Convergence Divergence)는 단기(12) EMA와 장기(26) EMA의 차이를 나타냄.
        •	MACD Line = 12-day EMA - 26-day EMA
        •	Signal Line = 9-day EMA of MACD Line (MACD의 9일 이동 평균)
        •	MACD와 Signal의 차이를 히스토그램으로 표현함. = MACD OSC
        """

        df['ema_short'] = df['Close'].ewm(span=short_window, adjust=False).mean()
        df['ema_long'] = df['Close'].ewm(span=long_window, adjust=False).mean()

        df['macd'] = (df['ema_short'] - df['ema_long']).round(2)
        df['macd_signal'] = (df['macd'].ewm(span=signal_window, adjust=False).mean()).round(2)
        df['macd_histogram'] = (df['macd'] - df['macd_signal']).round(2)  # MACD 히스토그램 = osc

        return df
    

    def cal_stochastic_df(self, df, k_window=14, d_window=3):
        """
        •	현재 종가가 최근 N일 동안의 고점과 저점 사이에서 어디쯤 위치하는지를 나타내는 지표.
        •	K% = (현재 종가 - 최저가) / (최고가 - 최저가) * 100
        •	D% = K%의 3일 이동 평균
        """

        df['low_min'] = df['Low'].rolling(window=k_window).min()
        df['high_max'] = df['High'].rolling(window=k_window).max()

        df['stochastic_k'] = (100 * ((df['Close'] - df['low_min']) / (df['high_max'] - df['low_min'] + 1e-10))).round(2)
        df['stochastic_d'] = (df['stochastic_k'].rolling(window=d_window).mean()).round(2)  # 3일 이동 평균

        return df


    def cal_ema_df(self, df, period):
        """
            DataFrame에서 EMA(지수이동평균)를 계산하여 추가합니다.
            :param df: 입력 DataFrame
            :param period: EMA 주기
            :param column: EMA를 계산할 컬럼 이름 (기본값: 'Close')
            :return: EMA 컬럼이 추가된 DataFrame
        """
        ema_column_name = f'EMA_{period}'
        df[ema_column_name] = (df['Close'].ewm(span=period, adjust=False).mean()).round(1)
        
        return df