# simulation.py
import time
import numpy as np
import pandas as pd
import requests
import math
import matplotlib.pyplot as plt
from pykis import PyKis, KisChart, KisStock, KisAuth
from datetime import datetime
import mplfinance as mpf
from dotenv import load_dotenv
import os
import json
from pykis import KisQuote
from pykis import KisBalance
from pykis import KisOrder
from pykis import KisRealtimePrice, KisSubscriptionEventArgs, KisWebsocketClient, PyKis
from pykis import PyKis, KisTradingHours
from pykis import PyKis, KisOrderProfits
from pykis import KisRealtimeExecution, KisSubscriptionEventArgs, KisWebsocketClient
from app.utils.auto_trading_stock import AutoTradingStock  # auto_trading.py에서 가져옴


class Simulation:
    def __init__(self, auto_trading_stock: AutoTradingStock): # 클래스 인스턴스가 생성될 때 호출되는 초기화 메소드
        self.auto_trading_stock = auto_trading_stock # 전달받은 AutoTradingStock 객체를 Simulation 클래스의 속성으로 저장
        
        # kis 속성 확인
        if not self.auto_trading_stock.kis:
            raise ValueError("❌ AutoTradingStock의 kis 속성이 초기화되지 않았습니다.")

    # 봉 데이터를 가져오는 함수
    def _get_ohlc(self, symbol, start_date, end_date):
        symbol_stock: KisStock = self.auto_trading_stock.kis.stock(symbol)  # SK하이닉스 (코스피)
        chart: KisChart = symbol_stock.chart(
            start=start_date,
            end=end_date,
        ) # 2023년 1월 1일부터 2023년 12월 31일까지의 일봉입니다.
        klines = chart.bars

        # 첫 번째 데이터를 제외하고, 각 항목의 open 값을 전날 close 값으로 변경
        for i in range(1, len(klines)):
            klines[i].open = klines[i - 1].close  # 전날의 close로 open 값을 변경
            
        return klines
        
    # 볼린저밴드 계산
    def _cal_bollinger_band(self, previous_closes, close_price):
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
    
        


    # 윗꼬리와 아랫꼬리를 체크하는 함수
    def _check_wick(self, candle, previous_closes, lower_band, sma, upper_band):
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


    def _draw_chart(self, symbol, ohlc, timestamps, buy_signals, sell_signals):

        # 캔들 차트 데이터프레임 생성
        df = pd.DataFrame(ohlc, columns=['Open', 'High', 'Low', 'Close'], index=pd.DatetimeIndex(timestamps))

        # 볼린저 밴드 계산
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['Upper'] = df['SMA'] + (df['Close'].rolling(window=20).std() * 2)
        df['Lower'] = df['SMA'] - (df['Close'].rolling(window=20).std() * 2)

        # 매수 및 매도 시그널 표시를 위한 추가 데이터 (x와 y의 길이 맞추기 위해 NaN 사용)
        df['Buy_Signal'] = np.nan
        df['Sell_Signal'] = np.nan

        for signal in buy_signals:
            df.at[signal[0], 'Buy_Signal'] = signal[1]
        for signal in sell_signals:
            df.at[signal[0], 'Sell_Signal'] = signal[1]

        # 그래프 그리기
        add_plot = [
            mpf.make_addplot(df['Upper'], color='blue', linestyle='-', label='Upper Band'),
            mpf.make_addplot(df['Lower'], color='blue', linestyle='-', label='Lower Band'),
            mpf.make_addplot(df['SMA'], color='orange', label='SMA'),
            mpf.make_addplot(df['Buy_Signal'], type='scatter', markersize=20, marker='^', color='green', label='BUY'),
            mpf.make_addplot(df['Sell_Signal'], type='scatter', markersize=20, marker='v', color='red', label='SELL')
        ]

        simulation_plot = mpf.plot(df, type='candle', style='charles', title=f'{symbol}', addplot=add_plot, ylabel='Price (KRW)', figsize=(20, 9), returnfig=True)

        return simulation_plot


    
    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw):
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)
        realized_pnl = 0
        position = 0  # 현재 포지션 수량
        trade_stack = []  # 매수 가격을 저장하는 스택
        previous_closes = []  # 이전 종가들을 저장
        total_invested = 0  # 매수에 사용된 총 금액
        current_cash = target_trade_value_krw  # 초기 잔고
    
    # 그래프 그리기 위한 데이터
        timestamps = []
        ohlc = []
        buy_signals = []
        sell_signals = []

        for i in range(len(ohlc_data) - 1):
            candle = ohlc_data[i]
            next_candle = ohlc_data[i + 1]

            open_price = float(candle.open)
            high_price = float(candle.high)
            low_price = float(candle.low)
            close_price = float(candle.close)
            timestamp = candle.time
            next_open_price = float(next_candle.open)
            next_timestamp = next_candle.time

            timestamps.append(timestamp)
            ohlc.append([open_price, high_price, low_price, close_price])

            previous_closes.append(close_price)

        # 볼린저 밴드 계산
            bollinger_band = self._cal_bollinger_band(previous_closes, close_price)

            upper_wick, lower_wick = self._check_wick(
                candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper']
        )

            if lower_wick and current_cash >= open_price:  # 매수 조건 및 잔고 확인
                position += 1
                trade_stack.append(open_price)
                buy_signals.append((timestamp, open_price))

                current_cash -= open_price  # 잔고 감소
                total_invested += open_price  # 투자 금액 증가

            # 매수 알림 전송
                message = (
                    f"📈 매수 이벤트 발생!\n"
                    f"종목: {symbol}\n"
                    f"매수가: {open_price:.2f} KRW\n"
                    f"매수 시점: {timestamp}\n"
                    f"총 포지션: {position}\n"
                    f"현재 잔고: {current_cash:.2f} KRW"
            )
                self.auto_trading_stock.send_discord_webhook(message, "simulation")

            elif upper_wick and position > 0:  # 매도 조건
                entry_price = trade_stack.pop()  # 매수 가격 가져오기
                exit_price = next_open_price  # 매도가
                pnl = exit_price - entry_price  # 개별 거래 손익
                realized_pnl += pnl  # 총 실현 손익에 추가
                sell_signals.append((next_timestamp, exit_price))
                position -= 1

                current_cash += exit_price  # 매도로 인한 잔고 증가

            # 매도 알림 전송
                message = (
                    f"📉 매도 이벤트 발생!\n"
                    f"종목: {symbol}\n"
                    f"매도가: {exit_price:.2f} KRW\n"
                    f"매도 시점: {next_timestamp}\n"
                    f"거래 손익: {pnl:.2f} KRW\n"
                    f"총 실현 손익: {realized_pnl:.2f} KRW\n"
                    f"현재 잔고: {current_cash:.2f} KRW\n"
                    f"남은 포지션: {position}"
                )
                self.auto_trading_stock.send_discord_webhook(message, "simulation")

    # 마지막 종가를 기준으로 평가
        final_close = float(ohlc_data[-1].close)
        if position > 0:
            current_pnl = (final_close - sum(trade_stack) / len(trade_stack)) * position  # 현재 평가 손익
        else:
            current_pnl = 0

    # 결과 출력
        total_assets = current_cash + (final_close * position)  # 총 자산 = 현금 + 보유 자산 평가액
        message = (
            f"📊 시뮬레이션 완료!\n"
            f"종목: {symbol}\n"
            f"기간: {start_date} ~ {end_date}\n"
            f"총 실현 손익: {realized_pnl:.2f} KRW\n"
            f"현재 평가 손익: {current_pnl:.2f} KRW\n"
            f"최종 잔고: {current_cash:.2f} KRW\n"
            f"총 자산 가치: {total_assets:.2f} KRW"
        )
        self.auto_trading_stock.send_discord_webhook(message, "simulation")

        # 캔들 차트 데이터프레임 생성
        simulation_plot = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)

        return simulation_plot, realized_pnl, current_cash
    
    
    # EMA 초기값을 이용한 RSI 계산 코드   
    def calculate_rsi(self, closes, window=14):
        """
        EMA 기반 RSI 계산
        Args:
            closes (list): 종가 데이터
            window (int): RSI 계산에 사용할 기간
        Returns:
            list: RSI 값 리스트
        """
        if len(closes) < window:
            print("[ERROR] 데이터가 충분하지 않아 RSI를 계산할 수 없습니다.")
            return [None] * len(closes)

        deltas = np.diff(closes)  # 종가 변화량 계산
        gains = np.maximum(deltas, 0)  # 상승폭(U)
        losses = np.maximum(-deltas, 0)  # 하락폭(D)

        # 초기 EMA 값 계산 (단순 평균 사용)
        ema_gain = np.mean(gains[:window])
        ema_loss = np.mean(losses[:window])

        # RSI 리스트 초기화
        rsi = [None] * (window - 1)  # 초기 n-1일은 RSI 계산 불가

        # 첫 RSI 계산
        rs = ema_gain / ema_loss if ema_loss != 0 else 0
        rsi.append(100 - (100 / (1 + rs)))

        # 이후 EMA 방식으로 RSI 계산
        for i in range(window, len(closes)):
            ema_gain = (ema_gain * (window - 1) + gains[i - 1]) / window
            ema_loss = (ema_loss * (window - 1) + losses[i - 1]) / window

            rs = ema_gain / ema_loss if ema_loss != 0 else 0
            rsi.append(100 - (100 / (1 + rs)))

        return rsi
    
    #초기값은 SMA 방식으로 계산
    # def calculate_rsi(self, closes, window=14):
    #     """
    #     RSI 계산
    #     Args:
    #         closes (list): 종가 데이터
    #         window (int): RSI 계산에 사용할 기간
    #     Returns:
    #         list: RSI 값 리스트
    #     """
    #     # 종가 데이터가 충분히 있는지 확인
    #     if len(closes) < window:
    #         print("[ERROR] 종가 데이터가 부족하여 RSI를 계산할 수 없습니다.")
    #         return [None] * len(closes)

    #     # 종가 차이 계산
    #     deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    #     gains = [max(delta, 0) for delta in deltas]
    #     losses = [-min(delta, 0) for delta in deltas]

    #     # 초기 평균 상승/하락폭 계산
    #     avg_gain = [0] * len(closes)
    #     avg_loss = [0] * len(closes)
    #     rsi = [None] * len(closes)

    #     avg_gain[window - 1] = sum(gains[:window]) / window
    #     avg_loss[window - 1] = sum(losses[:window]) / window

    #     # RSI 계산
    #     for i in range(window, len(closes)):
    #         # 이동 평균 계산
    #         avg_gain[i] = (avg_gain[i - 1] * (window - 1) + gains[i - 1]) / window
    #         avg_loss[i] = (avg_loss[i - 1] * (window - 1) + losses[i - 1]) / window

    #         # RS 및 RSI 계산
    #         if avg_loss[i] == 0:
    #             rs = 0
    #         else:
    #             rs = avg_gain[i] / avg_loss[i]
    #         rsi[i] = 100 - (100 / (1 + rs))

    #     return rsi
    
    def rsi_simulate_trading(self, symbol: str, start_date: str, end_date: str, 
                    rsi_window: int = 14, buy_threshold: int = 50, sell_threshold: int = 70):
        """
        RSI 매매 로직 및 시각화 데이터 포함
        Args:
            symbol (str): 종목 코드
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
            rsi_window (int): RSI 계산에 사용할 기간
            buy_threshold (float): RSI 매수 임계값
            sell_threshold (float): RSI 매도 임계값
        """
        # 문자열 날짜를 datetime.date 타입으로 변환
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        print(f"[DEBUG] RSI 매매 시작 - 종목: {symbol}, 기간: {start_date} ~ {end_date}")
        
        # OHLC 데이터 조회
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)

        # 초기화
        realized_pnl = 0  # 총 실현 손익
        position = 0  # 현재 포지션
        current_cash = 1_000_000  # 초기 자본
        buy_signals = []  # 매수 신호
        sell_signals = []  # 매도 신호

        # 그래프 데이터 저장용
        timestamps = []
        ohlc = []
        closes = []

        for candle in ohlc_data:
            open_price = float(candle.open)
            high_price = float(candle.high)
            low_price = float(candle.low)
            close_price = float(candle.close)
            timestamp = candle.time

            # OHLC 데이터 수집
            timestamps.append(timestamp)
            ohlc.append([open_price, high_price, low_price, close_price])
            closes.append(close_price)

        print(f"[DEBUG] 가져온 종가 데이터: {closes[:10]}... (총 {len(closes)} 개)")

        # RSI 계산
        rsi_values = self.calculate_rsi(closes, rsi_window)
        print(f"[DEBUG] 계산된 RSI 데이터: {rsi_values[:10]}... (총 {len(rsi_values)} 개)")

        for i in range(rsi_window, len(rsi_values)):
            close_price = closes[i]
            rsi = rsi_values[i]
            prev_rsi = rsi_values[i - 1]
            date = timestamps[i]

            # 디버깅 로그
            print(f"[DEBUG] 날짜: {date}, 종가: {close_price:.2f}, RSI: {rsi}, 이전 RSI: {prev_rsi}")

            # **RSI 값이 None인 경우 건너뜀**
            if rsi is None or prev_rsi is None:
                print("[DEBUG] RSI 값이 None입니다. 루프를 건너뜁니다.")
                continue

            # 매수 조건: RSI가 buy_threshold를 상향 돌파
            if rsi > buy_threshold and prev_rsi < buy_threshold and current_cash >= close_price:
                position += 1
                current_cash -= close_price
                buy_signals.append((date, close_price))
                print(f"[DEBUG] 📈 매수 발생! 날짜: {date}, 가격: {close_price:.2f}, RSI: {rsi}")
                self.auto_trading_stock.send_discord_webhook(
                    f"📈 매수 발생! 종목: {symbol}, 가격: {close_price}, RSI: {rsi:.2f}, 이전 RSI: {prev_rsi:.2f}, 시간: {date}",
                    "simulation"
                )

            # 매도 조건: RSI가 sell_threshold를 상향 돌파 후 다시 하락
            elif rsi < sell_threshold and prev_rsi > sell_threshold and position > 0:
                current_cash += close_price
                pnl = close_price - buy_signals[-1][1]  # 개별 거래 손익
                realized_pnl += pnl
                position -= 1
                sell_signals.append((date, close_price))
                print(f"[DEBUG] 📉 매도 발생! 날짜: {date}, 가격: {close_price:.2f}, RSI: {rsi}, 손익: {pnl:.2f}")
                self.auto_trading_stock.send_discord_webhook(
                    f"📉 매도 발생! 종목: {symbol}, 가격: {close_price}, RSI: {rsi:.2f}, 이전 RSI: {prev_rsi:.2f}, 시간: {date}, 손익: {pnl:.2f} KRW",
                    "simulation"
                )

        # 최종 평가
        final_assets = current_cash + (position * closes[-1] if position > 0 else 0)
        print(f"[DEBUG] 최종 평가 완료 - 최종 자산: {final_assets:.2f}, 총 실현 손익: {realized_pnl:.2f}")
        self.auto_trading_stock.send_discord_webhook(
            f"📊 RSI 매매 시뮬레이션 완료\n"
            f"종목: {symbol}\n"
            f"기간: {start_date} ~ {end_date}\n"
            f"최종 자산: {final_assets} KRW\n"
            f"현금 잔고: {current_cash} KRW\n"
            f"보유 주식 평가 금액: {(position * closes[-1])} KRW\n"
            f"총 실현 손익: {realized_pnl} KRW\n",
            "simulation"
        )

        # 캔들 차트 시각화
        simulation_plot = self.visualize_trades(symbol, ohlc, timestamps, buy_signals, sell_signals)
        return simulation_plot, buy_signals, sell_signals, final_assets, realized_pnl




    
    def visualize_trades(self, symbol, ohlc, timestamps, buy_signals, sell_signals):
        """
        매수/매도 신호를 포함한 거래 차트를 시각화합니다.
        Args:
            symbol (str): 종목 코드
            ohlc (list): OHLC 데이터 리스트 (각 요소는 [Open, High, Low, Close])
            timestamps (list): 타임스탬프 데이터 리스트
            buy_signals (list): 매수 신호 (각 요소는 (timestamp, price) 형태)
            sell_signals (list): 매도 신호 (각 요소는 (timestamp, price) 형태)
        Returns:
            matplotlib.figure.Figure: 생성된 차트의 Figure 객체
        """

        df = pd.DataFrame(ohlc, columns=["Open", "High", "Low", "Close"], index=pd.DatetimeIndex(timestamps))

        # 매수/매도 신호 열 추가 및 초기화
        df["Buy_Signal"] = pd.Series(index=df.index, dtype="float64")
        df["Sell_Signal"] = pd.Series(index=df.index, dtype="float64")

        for date, price in buy_signals:
            if date in df.index:
                df.at[date, "Buy_Signal"] = price

        for date, price in sell_signals:
            if date in df.index:
                df.at[date, "Sell_Signal"] = price
            
        # NaN 값 제거 또는 대체 (mplfinance에서 오류 방지)
        df["Buy_Signal"].fillna(0, inplace=True)
        df["Sell_Signal"].fillna(0, inplace=True)

        # mplfinance 추가 플롯 설정
        add_plots = [
            mpf.make_addplot(df["Buy_Signal"], type="scatter", markersize=100, marker="^", color="green", label="Buy Signal"),
            mpf.make_addplot(df["Sell_Signal"], type="scatter", markersize=100, marker="v", color="red", label="Sell Signal")
        ]

        # 캔들 차트 플롯 생성
        fig, ax = mpf.plot(
            df,
            type="candle",
            style="charles",
            title=f"{symbol} Trading Signals",
            ylabel="Price (KRW)",
            addplot=add_plots,
            returnfig=True,
            figsize=(20, 10)
        )

        return fig