import numpy as np


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
    #     # EMA 초기값을 이용한 RSI 계산 코드   
    # def calculate_rsi(self, closes, window=14):
    #     """
    #     EMA 기반 RSI 계산
    #     Args:
    #         closes (list): 종가 데이터
    #         window (int): RSI 계산에 사용할 기간
    #     Returns:
    #         list: RSI 값 리스트
    #     """
    #     if len(closes) < window:
    #         print("[ERROR] 데이터가 충분하지 않아 RSI를 계산할 수 없습니다.")
    #         return [None] * len(closes)

    #     deltas = np.diff(np.array(closes))  # 리스트를 NumPy 배열로 변환
    #     gains = np.maximum(deltas, 0)  # 상승폭(U)
    #     losses = np.maximum(-deltas, 0)  # 하락폭(D)

    #     # 초기 EMA 값 계산 (단순 평균 사용)
    #     ema_gain = np.mean(gains[:window])
    #     ema_loss = np.mean(losses[:window])

    #     # RSI 리스트 초기화
    #     rsi = [None] * (window - 1)  # 초기 n-1일은 RSI 계산 불가

    #     # 첫 RSI 계산
    #     rs = ema_gain / ema_loss if ema_loss != 0 else 0
    #     rsi.append(100 - (100 / (1 + rs)))

    #     # 이후 EMA 방식으로 RSI 계산
    #     for i in range(window, len(closes)):
    #         ema_gain = (ema_gain * (window - 1) + gains[i - 1]) / window
    #         ema_loss = (ema_loss * (window - 1) + losses[i - 1]) / window

    #         rs = ema_gain / ema_loss if ema_loss != 0 else 0
    #         rsi.append(100 - (100 / (1 + rs)))

    #     return rsi
    
    def calculate_rsi(self, closes, window=14):
        """
        RSI 계산
        Args:
            closes (list): 종가 데이터
            window (int): RSI 계산에 사용할 기간
        Returns:
            list: RSI 값 리스트
        """
        # 종가 데이터가 충분히 있는지 확인
        if len(closes) < 1:
            print("[ERROR] 종가 데이터가 부족하여 RSI를 계산할 수 없습니다.")
            return []

        # 종가 차이 계산
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [max(delta, 0) for delta in deltas]
        losses = [-min(delta, 0) for delta in deltas]

        # 초기화
        avg_gain = [0] * len(closes)
        avg_loss = [0] * len(closes)
        rsi = [None] * len(closes)

        # `window`보다 작은 날 계산 (단순 평균 사용)
        for i in range(1, min(window, len(closes))):
            avg_gain[i] = sum(gains[:i]) / i
            avg_loss[i] = sum(losses[:i]) / i
            if avg_loss[i] == 0:
                rs = 0
            else:
                rs = avg_gain[i] / avg_loss[i]
            rsi[i] = 100 - (100 / (1 + rs))

        # `window` 이상의 날 계산 (EMA 방식 사용)
        if len(closes) >= window:
            avg_gain[window - 1] = sum(gains[:window]) / window
            avg_loss[window - 1] = sum(losses[:window]) / window
            if avg_loss[window - 1] == 0:
                rsi[window - 1] = 100
            else:
                rs = avg_gain[window - 1] / avg_loss[window - 1]
                rsi[window - 1] = 100 - (100 / (1 + rs))

            for i in range(window, len(closes)):
                avg_gain[i] = (avg_gain[i - 1] * (window - 1) + gains[i - 1]) / window
                avg_loss[i] = (avg_loss[i - 1] * (window - 1) + losses[i - 1]) / window

                if avg_loss[i] == 0:
                    rsi[i] = 100
                else:
                    rs = avg_gain[i] / avg_loss[i]
                    rsi[i] = 100 - (100 / (1 + rs))

        return rsi
