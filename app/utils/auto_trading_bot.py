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
from app.utils.crud_sql import SQLExecutor
from app.utils.database import get_db, get_db_session


# 보조지표 클래스 선언
indicator = TechnicalIndicator()
logic = TradingLogic()

class AutoTradingBot:
    """
        실전투자와 모의투자를 선택적으로 설정 가능
    """
    def __init__(self, user_name, virtual=False, app_key=None, secret_key=None, account=None):
        
        sql_executor = SQLExecutor()

        query = """
            SELECT * FROM fsts.user_info
            WHERE name = :name;
        """

        params = {
            "name": user_name
        }

        with get_db_session() as db:
            result = sql_executor.execute_select(db, query, params)

        self.kis_id = result[0]['kis_id']
        self.app_key = result[0]['app_key']
        self.secret_key = result[0]['secret_key']
        self.account = result[0]['account']
        self.virtual = virtual
        self.virtual_kis_id = result[0]['virtual_kis_id']
        self.virtual_app_key = result[0]['virtual_app_key']
        self.virtual_secret_key = result[0]['virtual_secret_key']
        self.virtual_account = result[0]['virtual_account']

        # 임의로 app_key 및 secret_key 넣고 싶을 경우
        if app_key is not None and secret_key is not None and account is not None:
            if virtual is True:
                self.virual_app_key = app_key
                self.virual_secret_key = secret_key
                self.virual_account = account
            else:
                self.app_key = app_key
                self.secret_key = secret_key
                self.account = account

        # 모의투자용 PyKis 객체 생성
        if self.virtual:
            if not all([self.kis_id, self.app_key, self.secret_key, self.account, 
                        self.virtual_kis_id, self.virtual_app_key, self.virtual_secret_key, self.virtual_account]):
                raise ValueError("모의투자 정보를 완전히 제공해야 합니다.")
            
            self.kis = PyKis(
                id=self.kis_id,         # 한국투자증권 HTS ID
                appkey=self.app_key,    # 발급받은 App Key
                secretkey=self.secret_key, # 발급받은 App Secret
                account=self.virtual_account, # 계좌번호 (예: "12345678-01")
                virtual_id=self.virtual_kis_id,
                virtual_appkey=self.virtual_app_key,
                virtual_secretkey=self.virtual_secret_key,
                keep_token=True  # API 접속 토큰 자동 저장
            )
        # 실전투자용 PyKis 객체 생성
        else:
            self.kis = PyKis(
                id=self.kis_id,             # 한국투자증권 HTS ID
                appkey=self.app_key,    # 발급받은 App Key
                secretkey=self.secret_key, # 발급받은 App Secret
                account=self.account, # 계좌번호 (예: "12345678-01")
                keep_token=True           # 토큰 자동 갱신 여부
            )
                            
        print(f"{'모의투자' if self.virtual else '실전투자'} API 객체가 성공적으로 생성되었습니다.")


    def send_discord_webhook(self, message, bot_type):
        if bot_type == 'trading':
            webhook_url = 'https://discord.com/api/webhooks/1324331095583363122/wbpm4ZYV4gRZhaSywRp28ZWQrp_hJf8iiitISJrNYtAyt5NmBccYWAeYgcGd5pzh4jRK'  # 복사한 Discord 웹훅 URL로 변경
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
    def _get_ohlc(self, symbol, start_date, end_date, mode="default"):
        symbol_stock: KisStock = self.kis.stock(symbol)  # SK하이닉스 (코스피)
        chart: KisChart = symbol_stock.chart(
            start=start_date,
            end=end_date,
        ) # 2023년 1월 1일부터 2023년 12월 31일까지의 일봉입니다.
        klines = chart.bars

        # 첫 번째 데이터를 제외하고, 각 항목의 open 값을 전날 close 값으로 변경 
        # mode = continuous
        if mode == 'continuous':
            for i in range(1, len(klines)):
                klines[i].open = klines[i - 1].close  # 전날의 close로 open 값을 변경
            
        return klines


    def _draw_chart(self, symbol, ohlc, timestamps, buy_signals, sell_signals):

        # 캔들 차트 데이터프레임 생성
        df = pd.DataFrame(ohlc, columns=['Open', 'High', 'Low', 'Close', 'Volume'], index=pd.DatetimeIndex(timestamps))

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
            add_plot.append(mpf.make_addplot(df['Buy_Signal'], type='scatter', markersize=60, marker='^', color='black', label='BUY'))
        if len(sell_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Sell_Signal'], type='scatter', markersize=60, marker='v', color='black', label='SELL'))

        simulation_plot = mpf.plot(df, type='candle', style='charles', title=f'{symbol}', addplot=add_plot, volume=True, ylabel_lower='Volume', ylabel='Price(KRW)', figsize=(20, 9), returnfig=True)

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
                # total_quantity 가 팔고자 하는 양보다 적을 때
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
    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw, trading_logic='check_wick'):
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)
        trade_amount = target_trade_value_krw  # 매매 금액 (krw)
        position = 0  # 현재 포지션 수량
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
        while i < len(ohlc_data):
            candle = ohlc_data[i]

            open_price = float(candle.open)
            high_price = float(candle.high)
            low_price = float(candle.low)
            close_price = float(candle.close)
            volume = float(candle.volume)
            timestamp = candle.time

            timestamps.append(timestamp)
            ohlc.append([open_price, high_price, low_price, close_price, volume])

            # if len(previous_closes) >= 5:  # 최근 5개의 종가만 사용
            #     previous_closes.pop(0)
            previous_closes.append(close_price)
            
            # 매매 이력
            history = {}

            # initiate
            buy_yn = False
            sell_yn = False

            if trading_logic == 'check_wick':
                
                # 볼린저 밴드 계산
                bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                sma = indicator.cal_ma(previous_closes, 5)

                upper_wick, lower_wick = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])

                buy_yn = lower_wick # 아랫꼬리일 경우 매수 (추가 매수 가능)
                sell_yn = upper_wick and position > 0 # 윗꼬리일 때 매도. 매수한 횟수의 1/n 만큼 매도
            
            elif trading_logic == 'penetrating':
                pass


            if buy_yn: # 매수 (추가 매수 가능)
                history['position'] = 'BUY'
                history['price'] = close_price
                history['quantity'] = math.floor(trade_amount / close_price) # 특정 금액을 주기적으로 산다고 가정해서 주식 수 계산
                trading_history['history'].append(history)

                # draw 차트 위함
                buy_signals.append((timestamp, close_price))

                print(f"매수 시점: {timestamp}, 매수가: {close_price} KRW, 매수량: {history['quantity']}")

            elif sell_yn:  # 매수한 횟수의 1/n 만큼 매도
                history['position'] = 'SELL'
                history['price'] = close_price

                # 매도할수 있는 양이 대상 금액보다 적을 때
                if trading_history['total_quantity'] < math.floor(trade_amount / close_price):
                    history['quantity'] = trading_history['total_quantity']
                else:
                    history['quantity'] = math.floor(trade_amount / close_price) # 특정 금액을 주기적으로 산다고 가정해서 주식 수 계산

                trading_history['history'].append(history)

                sell_signals.append((timestamp, close_price))

                print(f"매도 시점: {timestamp}, 매도가: {close_price} KRW, 매도량: {history['quantity']}")
            
            result = self.calculate_pnl(trading_history, close_price)
            print(f"총 비용: {result['total_cost']}KRW, 총 보유량: {result['total_quantity']}주, 평균 단가: {result['average_price']}KRW, 실현 손익 (Realized PnL): {result['realized_pnl']}KRW, 미실현 손익 (Unrealized PnL): {result['unrealized_pnl']}KRW")

            # 현재 포지션 개수 (없는데 sell 하지 않기 위함)
            position = result['total_quantity']

            i += 1

        # 캔들 차트 데이터프레임 생성
        simulation_plot = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)

        return simulation_plot


    # 실시간 매매 함수
    def trade(self, symbol, symbol_name, start_date, end_date, target_trade_value_krw):
        
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)
        trade_amount = target_trade_value_krw  # 매매 금액 (krw)

        previous_closes = [float(candle.close) for candle in ohlc_data[:-2]]  # 마지막 봉을 제외한 종가들

        # 마지막 봉 데이터 (마지막 봉이란 당일)
        candle = ohlc_data[-1]
        open_price = float(candle.open)
        high_price = float(candle.high)
        low_price = float(candle.low)
        close_price = float(candle.close)
        timestamp = candle.time

        # 마지막 직전 봉 데이터
        previous_candle = ohlc_data[-2]
        prev_open_price = float(previous_candle.open)
        prev_close_price = float(previous_candle.close)
        
        # 볼린저 밴드 계산
        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
        
        # 로직 체크 (윗꼬리, 아랫꼬리)
        # 여기에 원하는 로직 호출
        upper_wick, lower_wick = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])

        # 마지막 직전 봉 음봉, 양봉 계산
        is_bearish_prev_candle = prev_close_price < prev_open_price  # 음봉 확인
        is_bullish_prev_candle = prev_close_price > prev_open_price  # 양봉 확인

        print(f'마지막 직전 봉 : {prev_close_price - prev_open_price}. 양봉 : {is_bullish_prev_candle}, 음봉 : {is_bearish_prev_candle}')

        # 최근 매매 기준 n% 변동성 미만일 경우 추가 매매 하지 않도로 설정
        # TO-DO

        # 매매 구현 (모든 로직이 true 일 경우)
        if lower_wick:  # 아랫꼬리일 경우 매수 (추가 매수 가능)
            pass
            # 매수 함수 구현
            self.send_discord_webhook(f"{symbol_name} 매수가 완료되었습니다. 매수금액 : {int(ohlc_data[-1].close)}KRW", "trading")
        elif upper_wick:  # 윗꼬리일 경우 매도 (매수한 횟수의 1/n 만큼 매도)
            pass
            # 매수 함수 구현
            self.send_discord_webhook(f"{symbol_name} 매도가 완료되었습니다. 매도금액 : {int(ohlc_data[-1].close)}KRW", "trading")
        
        # result = self.calculate_pnl(trading_history, close_price)
        # print(f"총 비용: {result['total_cost']}KRW, 총 보유량: {result['total_quantity']}주, 평균 단가: {result['average_price']}KRW, 실현 손익 (Realized PnL): {result['realized_pnl']}KRW, 미실현 손익 (Unrealized PnL): {result['unrealized_pnl']}KRW")
    

        # 가격 조회
        # DB 에서 종목 조회
        # 체결 강도 로직 조회

        return None
    

    # 컷 로스 (손절)
    def cut_loss(self, target_trade_value_usdt):
        pass