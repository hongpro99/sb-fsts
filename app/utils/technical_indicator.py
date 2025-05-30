import numpy as np
import pandas as pd


class TechnicalIndicator:
    
    def cal_bollinger_band(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        df에 볼린저 밴드 지표(Upper, Middle, Lower)를 추가하여 반환합니다.
        - Middle: 단순 이동 평균(SMA)
        - Upper: Middle + (표준편차 * 2)
        - Lower: Middle - (표준편차 * 2)
        - 표준편차 승수: 2
        - 표준편차 계산 방식: 모집단 기준 (ddof=0)
        
        Parameters:
            df (pd.DataFrame): OHLC 데이터프레임, 'Close' 컬럼이 반드시 있어야 함
            window (int): 볼린저밴드 계산에 사용할 이동평균 구간 (기본값 20일)

        Returns:
            pd.DataFrame: 볼린저밴드 컬럼이 추가된 DataFrame
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame에 'Close' 컬럼이 필요합니다.")

        # rolling = df['Close'].rolling(window=window)
        # df['BB_Middle'] = rolling.mean()
        # df['BB_Std'] = rolling.std()
        # df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        # df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
            # 볼린저 밴드 계산

        df['BB_Middle'] = df['Close'].rolling(window=window).mean()
        df['BB_Std'] = df['Close'].rolling(window=window).apply(lambda x: np.std(x, ddof=0), raw=True)
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)

        df.drop(columns=['BB_Std'], inplace=True)  # 표준편차 임시 컬럼 제거

        return df

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

    def cal_rsi_df(self, df, period=25):
        """
        단순이동평균으로 계산한 표준 RSI
        delta = 오늘 종가 - 어제 종가
        gain = 양의 delta (음수는 0으로)
        loss = 음의 delta의 절댓값 (양수는 0으로)
        avg_gain = 14일간 평균 gain
        avg_loss = 14일간 평균 loss
        RS = avg_gain / avg_loss
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
    

    def cal_macd_df(self, df, short_window=12, long_window=26, signal_window=9, round_digits=2):
        """
        MACD 오실레이터
        •	MACD (Moving Average Convergence Divergence)는 단기(12) EMA와 장기(26) EMA의 차이를 나타냄.
        •	MACD Line = 12-day EMA - 26-day EMA
        •	Signal Line = 9-day EMA of MACD Line (MACD의 9일 이동 평균)
        •	MACD와 Signal의 차이를 히스토그램으로 표현함. = MACD OSC
        테스트 결과 ??
        """

        # 단기 EMA
        df['ema_short'] = df['Close'].ewm(span=short_window, adjust=False).mean()

        # 장기 EMA
        df['ema_long'] = df['Close'].ewm(span=long_window, adjust=False).mean()

        # MACD
        df['macd'] = df['ema_short'] - df['ema_long']

        # Signal (MACD의 EMA)
        df['macd_signal'] = df['macd'].ewm(span=signal_window, adjust=False).mean()

        # Histogram
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # 반올림 (optional)
        df['ema_short'] = df['ema_short'].round(round_digits)
        df['ema_long'] = df['ema_long'].round(round_digits)
        df['macd'] = df['macd'].round(round_digits)
        df['macd_signal'] = df['macd_signal'].round(round_digits)
        df['macd_histogram'] = df['macd_histogram'].round(round_digits)

        return df
    

    def cal_stochastic_df(self, df, k_period=14, k_smoothing=3, d_period=3, round_digits=2):
        """
        Stochastic Slow (14,3,3) 계산 함수
        - Fast %K: (종가 - 최저가) / (최고가 - 최저가) * 100
        - Slow %K: Fast %K의 k_smoothing일 단순이동평균
        - Slow %D: Slow %K의 d_period일 단순이동평균

        :param df: OHLC DataFrame (필수 컬럼: 'High', 'Low', 'Close')
        :return: df with 'slow_k', 'slow_d' 컬럼 추가
        테스트 결과 비슷함
        """

        # Fast %K 계산
        low_min = df['Low'].rolling(window=k_period, min_periods=1).min()
        high_max = df['High'].rolling(window=k_period, min_periods=1).max()
        fast_k = (df['Close'] - low_min) / (high_max - low_min) * 100

        # Slow %K: Fast %K의 EMA
        slow_k = fast_k.ewm(span=k_smoothing, adjust=True).mean()

        # Slow %D: Slow %K의 EMA
        slow_d = slow_k.ewm(span=d_period, adjust=True).mean()

        # 결과 반올림
        df['stochastic_k'] = slow_k.round(round_digits)
        df['stochastic_d'] = slow_d.round(round_digits)

        return df


    def cal_ema_df(self, df, period, round_digits=0):
        """
            DataFrame에서 EMA(지수이동평균)를 계산하여 추가합니다.
            :param df: 입력 DataFrame
            :param period: EMA 주기
            :param column: EMA를 계산할 컬럼 이름 (기본값: 'Close')
            :return: EMA 컬럼이 추가된 DataFrame
            adjust= True, False 차이로 값이 다름. True와 False 모두 다른 증권사와는 값이 차이가 있음.
            True = 가중합식, False = 재귀식
        """
        
        ema_column_name = f'EMA_{period}'
        
        df[ema_column_name] = df['Close'].ewm(span=period, adjust=True).mean()
        df[ema_column_name] = df[ema_column_name].round(round_digits)
        
        return df
    
    def cal_sma_df(self, df, period, round_digits=1):
        """
        DataFrame에서 SMA(단순이동평균)를 계산하여 추가합니다.
        
        :param df: 입력 DataFrame
        :param period: SMA 주기
        :param round_digits: 반올림 자릿수 (기본값: 1)
        :return: SMA 컬럼이 추가된 DataFrame
        """
        
        sma_column_name = f'SMA_{period}'
        
        df[sma_column_name] = df['Close'].rolling(window=period).mean()
        df[sma_column_name] = df[sma_column_name].round(round_digits)
        
        return df
    
    def cal_horizontal_levels_df(self, df, lookback_prev=5, lookback_next=5):
        """
        df에 고점/저점 수평선 컬럼을 추가
        - 'horizontal_high': 해당 행이 고점 수평선이면 값
        - 'horizontal_low': 해당 행이 저점 수평선이면 값
        """
        df = df.copy()
        df['horizontal_high'] = None
        df['horizontal_low'] = None

        for i in range(lookback_prev, len(df) - lookback_next):
            window = df.iloc[i - lookback_prev : i + lookback_next + 1]
            center = df.iloc[i]

        if center['High'] == window['High'].max():
            df.at[df.index[i], 'horizontal_high'] = center['High']
        if center['Low'] == window['Low'].min():
            df.at[df.index[i], 'horizontal_low'] = center['Low']

        return df
    
    def extend_trendline_from_points(self, x_vals, y_vals, target_x):
        try:
            # 💡 명시적 float 변환으로 numpy가 에러 없이 처리할 수 있게 함
            x_vals = np.array(x_vals, dtype=float)
            y_vals = np.array(y_vals, dtype=float)
            target_x = float(target_x)
    

            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            print(f"slope: {slope}")
            if slope >= 0:
                return None  # ❌ 하락 추세선만 허용
            return slope * target_x + intercept
        except Exception as e:
            print(f"[❌ 추세선 계산 에러] {e}")
            return None


    def get_latest_trendline_from_highs(self, df, current_idx, window=2, lookback_next=5):
        """
        최근 확정된 horizontal_high 기반 고점 추세선을 window개로 만들고 current_idx까지 연장
        여러 개의 확정된 고점을 기반으로 기울어진 선을 계산
        """
        max_idx = current_idx - lookback_next
        if max_idx <= 0:
            return None

        confirmed_highs = df.iloc[:max_idx][df['horizontal_high'].notna()]
        if confirmed_highs.empty:
            return None

        highs_window = confirmed_highs.iloc[-window:] if len(confirmed_highs) >= window else confirmed_highs
        if len(highs_window) < 2:
            return None

        x_vals = [df.index.get_loc(idx) for idx in highs_window.index]
        y_vals = highs_window['horizontal_high'].values
        target_x = current_idx

        print("📊 Trendline Debug Info")
        print("🟨 고점 날짜 인덱스:", highs_window.index.tolist())
        print("🟧 x_vals:", x_vals)
        print("🟥 y_vals:", y_vals)
        # try:
        #     slope, intercept = np.polyfit(x_vals, y_vals, 1)
        #     if slope >= 0:
        #         return None  # ❌ 하락 추세선만 허용
        #     return slope * target_x + intercept
        # except Exception as e:
        #     print(f"[❌ 추세선 계산 에러] {e}")
        #     return None
        
        return self.extend_trendline_from_points(x_vals, y_vals, target_x)
    
    def add_extended_high_trendline(self, df, window=2, lookback_next=5):
        """
        df에 각 시점의 고점 추세선을 연장한 값을 계산하여 컬럼으로 추가
        """
        df = df.copy()
        extended_trendline = []

        for i in range(len(df)):
            if i < window + lookback_next:
                extended_trendline.append(None)
            else:
                trend_val = self.get_latest_trendline_from_highs(df, current_idx=i, window=window, lookback_next=lookback_next)
                extended_trendline.append(trend_val)

        df['extended_high_trendline'] = extended_trendline
        return df
