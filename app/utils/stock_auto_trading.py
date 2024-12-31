import datetime
import numpy as np
import pandas as pd
import requests
import math
from pykis import PyKis, KisChart, KisStock
from datetime import date, time
import mplfinance as mpf

from app.utils.technical_indicator import TechnicalIndicator
from app.utils.trading_logic import TradingLogic


API_KEY = "8aChkjQ9XijCL3LwC7LGJuDrn3FVFh62g9WPEaa0UnwmGt7hsu8tKBk61hQd76YG"
API_SECRET = "YznqQReI62NOd7QQfaPSXk6whFrQxyraId9iEcwtUScNtCq7tTGHugM7kYv77SpP"

# 보조지표 클래스 선언
indicator = TechnicalIndicator()
logic = TradingLogic()

class AutoTradingStock:
    def __init__(self, api_key=API_KEY, api_secret=API_SECRET):
        
        # 개인 계정으로 변경해야 함. env 파일로 빼는게 좋을 듯!
        self.kis = PyKis(
            id="YOUR_ID",             # 한국투자증권 HTS ID
            appkey="PSyTGF07QupJyV76XGm3mkgcr4RDvSeODpVZ",    # 발급받은 App Key
            secretkey="eteoHNN+iHktbHC1TOKNdDc2ecFHqwyA+o1OijESqRtWY2cirhUqbiuFfO5zmEPNqB8/P0RSBuTjZnPq4zc5u3dKHIg/HOFQqmZcCik621aWqti5MBReqNpr/NChcs8edoBKd4cgJaC47m3IKncU4GglKzWNqHtic/4X8lmOAZx0oDGuFkI=", # 발급받은 App Secret
            account="67737279", # 계좌번호 (예: "12345678-01")
            keep_token=True           # 토큰 자동 갱신 여부
        )

    def send_discord_webhook(self, message, bot_type):
        if bot_type == 'trading':
            webhook_url = 'https://discord.com/api/webhooks/1313346849838596106/6Rn_8BNDeL9bMYfFtqscpu4hPah5c2RsNl0rBiPoSw_Qb9RXgDdVHoHmwEuStPv_ufnV'  # 복사한 Discord 웹훅 URL로 변경
            username = "Stock Trading Bot"

        data = {
            "content": message,
            "username": username,  # 원하는 이름으로 설정 가능
        }
        
        # 요청 보내기
        response = requests.post(webhook_url, json=data)
        
        # 응답 확인
        if response.status_code == 204:
            print("메시지가 성공적으로 전송되었습니다.")
        else:
            print(f"메시지 전송 실패: {response.status_code}, {response.text}")


    # 봉 데이터를 가져오는 함수
    def _get_ohlc(self, symbol, start_date, end_date):
        symbol_stock: KisStock = self.kis.stock(symbol)  # SK하이닉스 (코스피)
        chart: KisChart = symbol_stock.chart(
            start=start_date,
            end=end_date,
        ) # 2023년 1월 1일부터 2023년 12월 31일까지의 일봉입니다.
        klines = chart.bars

        # 첫 번째 데이터를 제외하고, 각 항목의 open 값을 전날 close 값으로 변경
        for i in range(1, len(klines)):
            klines[i].open = klines[i - 1].close  # 전날의 close로 open 값을 변경
            
        return klines


    def _draw_chart(self, symbol, ohlc, timestamps, buy_signals, sell_signals):

        # 캔들 차트 데이터프레임 생성
        df = pd.DataFrame(ohlc, columns=['Open', 'High', 'Low', 'Close'], index=pd.DatetimeIndex(timestamps))

        # 볼린저 밴드 계산
        df['Middle'] = df['Close'].rolling(window=20).mean()
        df['Upper'] = df['Middle'] + (df['Close'].rolling(window=20).std() * 2)
        df['Lower'] = df['Middle'] - (df['Close'].rolling(window=20).std() * 2)

        # MA 계산
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_13'] = df['Close'].rolling(window=13).mean()
        df['SMA_60'] = df['Close'].rolling(window=60).mean()
        df['SMA_120'] = df['Close'].rolling(window=120).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # 매수 및 매도 시그널 표시를 위한 추가 데이터 (x와 y의 길이 맞추기 위해 NaN 사용)
        df['Buy_Signal'] = np.nan
        df['Sell_Signal'] = np.nan

        for signal in buy_signals:
            if signal[0] in df.index:  # signal[0]이 인덱스에 존재하는 경우만 처리
                df.at[signal[0], 'Buy_Signal'] = signal[1]
        for signal in sell_signals:
            if signal[0] in df.index:  # signal[0]이 인덱스에 존재하는 경우만 처리
                df.at[signal[0], 'Sell_Signal'] = signal[1]

        # 그래프 그리기
        add_plot = [
            mpf.make_addplot(df['Upper'], color='blue', linestyle='-', label='Upper Band'),
            mpf.make_addplot(df['Lower'], color='blue', linestyle='-', label='Lower Band'),
            mpf.make_addplot(df['Middle'], color='blue', linestyle='-', label='Middle Band'),
            mpf.make_addplot(df['SMA_5'], color='black', linestyle='-', label='SMA 5'),
            mpf.make_addplot(df['SMA_13'], color='red', linestyle='-', label='SMA 13'),
            mpf.make_addplot(df['SMA_60'], color='green', linestyle='-', label='SMA 60'),
            mpf.make_addplot(df['SMA_120'], color='purple', linestyle='-', label='SMA 120'),
            mpf.make_addplot(df['SMA_200'], color='gray', linestyle='-', label='SMA 200'),
        ]

        # signal이 존재할 때만 가능
        if len(buy_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Buy_Signal'], type='scatter', markersize=20, marker='^', color='green', label='BUY'))
        if len(sell_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Sell_Signal'], type='scatter', markersize=20, marker='v', color='red', label='SELL'))

        simulation_plot = mpf.plot(df, type='candle', style='charles', title=f'{symbol}', addplot=add_plot, ylabel='Price (KRW)', figsize=(20, 9), returnfig=True)

        return simulation_plot


    def calculate_pnl(self, trading_history, current_price):
        total_cost = 0  # 총 비용
        total_quantity = 0  # 총 수량
        realized_pnl = 0  # 실현 손익

        for trade in trading_history['history']:
            if trade['position'] == 'BUY':  # 매수일 경우
                total_cost += trade['price'] * trade['quantity']  # 비용 증가
                total_quantity += trade['quantity']  # 수량 증가

            elif trade['position'] == 'SELL':  # 매도일 경우
                if total_quantity == 0:
                    raise ValueError("매도 수량이 매수 수량보다 많습니다.")
                
                # 매도의 실현 손익 계산
                sell_quantity = trade['quantity']
                sell_price = trade['price']
                
                # 평균 단가로 계산
                average_price = total_cost / total_quantity if total_quantity > 0 else 0
                realized_pnl += (sell_price - average_price) * sell_quantity
                
                # 매도 후 수량 및 비용 감소
                total_quantity -= sell_quantity
                total_cost -= average_price * sell_quantity
            
            # 모든 주식을 매도했을 경우 비용 리셋
            if total_quantity == 0:
                total_cost = 0

        # 평균 단가
        average_price = total_cost / total_quantity if total_quantity > 0 else 0

        # 미실현 손익 계산
        unrealized_pnl = (current_price - average_price) * total_quantity if total_quantity > 0 else 0

        # 결과 저장
        trading_history['average_price'] = average_price
        trading_history['realized_pnl'] = realized_pnl
        trading_history['unrealized_pnl'] = unrealized_pnl
        trading_history['total_cost'] = total_cost
        trading_history['total_quantity'] = total_quantity
        
        return trading_history


    # 실시간 매매 시뮬레이션 함수
    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw):
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)
        realized_pnl = 0
        trade_amount = target_trade_value_krw  # 매매 금액 (krw)
        position = 0  # 현재 포지션 수량
        total_buy_budget = 0  # 총 매수 가격
        trade_stack = []  # 매수 가격을 저장하는 스택
        previous_closes = []  # 이전 종가들을 저장

        trading_history = {
            'average_price' : 0,  # 총 비용
            'realized_pnl' : 0,  # 총 수량
            'unrealized_pnl' : 0,  # 실현 손익
            'history' : []
        } # 트레이드 기록 저장

        # 그래프 그리기 위한 데이터
        timestamps = []
        ohlc = []
        buy_signals = []
        sell_signals = []

        i = 0
        while i < len(ohlc_data) - 1:
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

            # if len(previous_closes) >= 5:  # 최근 5개의 종가만 사용
            #     previous_closes.pop(0)
            previous_closes.append(close_price)

            # 볼린저 밴드 계산
            bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
            sma = indicator.cal_ma(previous_closes, 5)

            upper_wick, lower_wick = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])

            history = {}

            if lower_wick:  # 아랫꼬리일 경우 매수 (추가 매수 가능)
                position += 1
                trade_stack.append(open_price)

                history['position'] = 'BUY'
                history['price'] = open_price
                history['quantity'] = math.floor(trade_amount / open_price) # 특정 금액을 주기적으로 산다고 가정해서 주식 수 계산
                trading_history['history'].append(history)

                # draw 차트 위함
                buy_signals.append((timestamp, open_price))

                # total_buy_budget += open_price * (trade_amount / open_price)  # 총 매수 금액 누적
                # # 평균 매수 단가 계산
                # average_entry_price = total_buy_budget / position

                print(f"매수 시점: {timestamp}, 매수가: {open_price} KRW, 매수량: {history['quantity']}")

            elif upper_wick and position > 0:  # 윗꼬리일 경우 매도 (매수한 횟수의 1/n 만큼 매도)
                exit_price = next_open_price
                entry_price = trade_stack.pop()  # 스택에서 매수 가격을 가져옴
                pnl = (exit_price - entry_price) * math.floor(trade_amount / entry_price) # 주식 수 연산 및 곱하기
                realized_pnl += pnl

                history['position'] = 'SELL'
                history['price'] = open_price
                history['quantity'] = math.floor(trade_amount / open_price) # 특정 금액을 주기적으로 산다고 가정해서 주식 수 계산
                trading_history['history'].append(history)

                sell_signals.append((timestamp, open_price))
                position -= 1

                total_buy_budget -= entry_price * (trade_amount / entry_price)  # 매도 시 매수 금액에서 차감
                # 평균 매수 단가 계산
                average_entry_price = total_buy_budget / position if position > 0 else 0

                print(f"매도 시점: {timestamp}, 매도가: {open_price} KRW, 매도량: {history['quantity']}")
            
            if trading_history.get('history', None) is not None:
                result = self.calculate_pnl(trading_history, close_price)
                print(f"총 비용: {result['total_cost']}KRW, 총 보유량: {result['total_quantity']}주, 평균 단가: {result['average_price']}KRW, 실현 손익 (Realized PnL): {result['realized_pnl']}KRW, 미실현 손익 (Unrealized PnL): {result['unrealized_pnl']}KRW")
            else:
                print("아직 매매 기록이 없습니다.")

            i += 1

        # 캔들 차트 데이터프레임 생성
        simulation_plot = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)

        return simulation_plot


    # 실시간 매매 함수
    def trade(self):
        
        trading_logic = TradingLogic()

        # 가격 조회
        # DB 에서 종목 조회
        # 체결 강도 로직 조회
        is_buy_signal = trading_logic.func1()
        # 매수 함수
        if is_buy_signal is True:
            # 매수
            pass

        return None