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
