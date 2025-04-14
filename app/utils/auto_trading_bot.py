import datetime
import numpy as np
import pandas as pd
import requests
import math
import json
from pykis import PyKis, KisChart, KisStock, KisQuote
from datetime import datetime, date, time
import mplfinance as mpf
from pytz import timezone
from app.utils.dynamodb.model.simulation_history_model import SimulationHistory
from app.utils.technical_indicator import TechnicalIndicator
from app.utils.trading_logic import TradingLogic
from app.utils.crud_sql import SQLExecutor
from app.utils.dynamodb.crud import DynamoDBExecutor
from app.utils.database import get_db, get_db_session
from app.utils.dynamodb.model.trading_history_model import TradingHistory
from app.utils.dynamodb.model.auto_trading_model import AutoTrading
from app.utils.dynamodb.model.auto_trading_balance_model import AutoTradingBalance
from app.utils.dynamodb.model.user_info_model import UserInfo
from pykis import KisBalance
from decimal import Decimal


# 보조지표 클래스 선언
indicator = TechnicalIndicator()
logic = TradingLogic()

class AutoTradingBot:
    """
        실전투자와 모의투자를 선택적으로 설정 가능
    """
    def __init__(self, id, virtual=False, app_key=None, secret_key=None, account=None):
        
        # sql_executor = SQLExecutor()

        # query = """
        #     SELECT * FROM fsts.user_info
        #     WHERE name = :name;
        # """

        # params = {
        #     "name": user_name
        # }

        # with get_db_session() as db:
        #     result = sql_executor.execute_select(db, query, params)
            
        # if not result:
        #     raise ValueError(f"사용자 {user_name}에 대한 정보를 찾을 수 없습니다.")

        result = list(UserInfo.scan(
            filter_condition=(UserInfo.id == id)
        ))

        if len(result) == 0:
            raise ValueError(f"사용자 {id}에 대한 정보를 찾을 수 없습니다.")

        self.kis_id = result[0].kis_id
        self.app_key = result[0].app_key
        self.secret_key = result[0].secret_key
        self.account = result[0].account
        self.virtual = virtual
        self.virtual_kis_id = result[0].virtual_kis_id
        self.virtual_app_key = result[0].virtual_app_key
        self.virtual_secret_key = result[0].virtual_secret_key
        self.virtual_account = result[0].virtual_account

        # 임의로 app_key 및 secret_key 넣고 싶을 경우
        if app_key and secret_key and account:
            if virtual:
                self.virual_app_key = app_key
                self.virual_secret_key = secret_key
                self.virual_account = account
            else:
                self.app_key = app_key
                self.secret_key = secret_key
                self.account = account

        # PyKis 객체 생성
        self.create_kis_object()    

    def create_kis_object(self):
        """한 번 발급받은 토큰을 유지하면서 PyKis 객체 생성"""
        # 모의투자용 PyKis 객체 생성
        if self.virtual:
            if not all([self.kis_id, self.app_key, self.secret_key, 
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
        if bot_type == 'alarm':
            webhook_url = 'https://discord.com/api/webhooks/1313346849838596106/6Rn_8BNDeL9bMYfFtqscpu4hPah5c2RsNl0rBiPoSw_Qb9RXgDdVHoHmwEuStPv_ufnV'
            username = 'Stock Alarm Bot'
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
    def _get_ohlc(self, symbol, start_date, end_date, interval='day', mode="default"):
        symbol_stock: KisStock = self.kis.stock(symbol)  # SK하이닉스 (코스피)
        chart: KisChart = symbol_stock.chart(
            start=start_date,
            end=end_date,
            period=interval
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
        df = pd.DataFrame(ohlc, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'], index=pd.DatetimeIndex(timestamps))

        # 볼린저 밴드 계산
        df['Middle'] = df['Close'].rolling(window=20).mean()
        df['Upper'] = df['Middle'] + (df['Close'].rolling(window=20).std() * 2)
        df['Lower'] = df['Middle'] - (df['Close'].rolling(window=20).std() * 2)

        #sma
        df = indicator.cal_sma_df(df, 5)
        df = indicator.cal_sma_df(df, 20)
        df = indicator.cal_sma_df(df, 40)
        df = indicator.cal_sma_df(df, 120)
        df = indicator.cal_sma_df(df, 200)        

        #ema
        df = indicator.cal_ema_df(df, 10)
        df = indicator.cal_ema_df(df, 20)
        df = indicator.cal_ema_df(df, 50)
        df = indicator.cal_ema_df(df, 60)

        df = indicator.cal_rsi_df(df)
        df = indicator.cal_macd_df(df)
        df = indicator.cal_stochastic_df(df)
        df = indicator.cal_mfi_df(df)

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
        ]

        # # MA 를 그릴 수 있는 경우에만
        # if df['SMA_60'].notna().any():
        #     add_plot.append(mpf.make_addplot(df['SMA_60'], color='red', linestyle='-', label='SMA 60'))
        # if df['SMA_120'].notna().any():
        #     add_plot.append(mpf.make_addplot(df['SMA_120'], color='purple', linestyle='-', label='SMA 120'))
        # if df['SMA_200'].notna().any():
        #     add_plot.append(mpf.make_addplot(df['SMA_200'], color='gray', linestyle='-', label='SMA 200'))

        # signal이 존재할 때만 가능
        if len(buy_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Buy_Signal'], type='scatter', markersize=60, marker='^', color='black', label='BUY'))
        if len(sell_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Sell_Signal'], type='scatter', markersize=60, marker='v', color='black', label='SELL'))

        #simulation_plot = mpf.plot(df, type='candle', style='charles', title=f'{symbol}', addplot=add_plot, volume=True, ylabel_lower='Volume', ylabel='Price(KRW)', figsize=(20, 9), returnfig=True)

        return df


    def calculate_pnl(self, trading_history, current_price):
        """Parameters:
        - trading_history: dict, 거래 내역 및 계산 결과 저장
        - current_price: float, 현재 가격
        -initial_capital: 초기 자본
        """
        
        total_cost = 0  # 총 비용
        total_quantity = 0  # 총 수량
        total_realized_pnl = 0  # 실현 손익
        buy_count = 0  # 총 매수 횟수
        sell_count = 0  # 총 매도 횟수
        buy_dates = []  # 매수 날짜 목록
        sell_dates = []  # 매도 날짜 목록
        investment_cost = 0
        
        # 포지션별 계산
        for trade in trading_history['history']:
            
            if trade['position'] == 'BUY':  # 매수일 경우
                # 매수수의 실현 손익 계산
                buy_quantity = trade['quantity']
                buy_price = trade['price']
                                
                total_cost += buy_price * buy_quantity  # 비용 증가
                investment_cost += buy_price * buy_quantity
                total_quantity += buy_quantity  # 수량 증가
                buy_count += 1  # 매수 횟수 증가
                buy_dates.append(trade['time'])  # 매수 날짜 추가
                
            elif trade['position'] == 'SELL':  # 매도일 경우
                if total_quantity <= 0:
                    raise ValueError("포지션 수량이 없습니다!")
                    
                # 매도의 실현 손익 계산
                sell_quantity = trade['quantity']
                sell_price = trade['price']
                
                # 평균가 계산
                average_price = total_cost / total_quantity if total_quantity > 0 else 0
                
                #평균가로 매도 손익 계산
                total_realized_pnl += (sell_price - average_price) * sell_quantity
                
                # 매도 후 수량 및 비용 감소
                total_quantity -= sell_quantity
                total_cost -= average_price * sell_quantity
                #비용이 음수가 되지 않도록 처리
                total_cost = max(total_cost, 0)
                
                sell_count += 1  # 매도 횟수 증가
                sell_dates.append(trade['time'])  # 매도 날짜 추가
            
            # 모든 주식을 매도했을 경우 비용 리셋
            if total_quantity == 0:
                total_cost = 0
                
        # 평균 단가 계산(잔여 수량이 있는 경우)
        average_price = total_cost / total_quantity if total_quantity > 0 else 0

        # 미실현 손익 계산
        unrealized_pnl = (current_price - average_price) * total_quantity if total_quantity > 0 else 0
        realized_roi = (total_realized_pnl/investment_cost)*100 if investment_cost > 0 else 0
        unrealized_roi = ((total_realized_pnl + unrealized_pnl)/investment_cost)*100 if investment_cost > 0 else 0

        # 결과 저장
        trading_history.update({
            'average_price': average_price,  # 평균 매수 가격
            'realized_pnl': total_realized_pnl,  # 실현 손익
            'unrealized_pnl': unrealized_pnl,  # 미실현 손익
            'realized_roi' : realized_roi,
            'unrealized_roi' : unrealized_roi,
            'total_cost': total_cost,  # 총 매수 비용
            'total_quantity': total_quantity,  # 총 보유 수량
            'buy_count': buy_count,  # 매수 횟수
            'sell_count': sell_count,  # 매도 횟수
            'buy_dates': buy_dates,  # 매수 날짜 목록
            'sell_dates': sell_dates,  # 매도 날짜 목록
        })
        
        print(f"투자비용: {investment_cost}")
        return trading_history
    

    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw, buy_trading_logic=None, sell_trading_logic=None,
                        interval='day', buy_percentage = None, ohlc_mode = 'default', initial_capital=None, rsi_buy_threshold = 30, rsi_sell_threshold = 70, rsi_period = 25):
    
        ohlc_data = self._get_ohlc(symbol, start_date, end_date, interval, ohlc_mode) #클래스 객체, .사용
        # trade_reasons = logic.trade_reasons
        logic.trade_reasons = []
        # ✅ trade_reasons 초기화
        trade_reasons = []        
        #실제 투자 모드인지 확인
            # ✅ 실제 투자 모드인지 확인
        real_trading = initial_capital is not None

        # 기존 변수 초기화    
        trade_amount = target_trade_value_krw  # 매매 금액 (krw)
        position_count = 0  # 현재 포지션 수량
        positions = [] #손절 포지션
        previous_closes = []  # 이전 종가들을 저장
        closes = []
        trading_history = {
            'average_price': 0,  # 평단가
            'realized_pnl': 0,  # 실현 손익
            'unrealized_pnl': 0,  # 미실현 손익
            'realized_roi' : 0, #실현 수익률
            'unrealized_roi' : 0, # 총 수익률
            'total_cost': 0,  # 총 비용
            'total_quantity': 0,  # 총 수량
            'buy_count': 0,  # 총 매수 횟수
            'sell_count': 0,  # 총 매도 횟수
            'buy_dates': [],  # 매수 날짜 목록
            'sell_dates': [],  # 매도 날짜 목록
            'history': [],  # 거래 내역
            'initial_capital': initial_capital
        }

        # 그래프 그리기 위한 데이터
        timestamps = []
        ohlc = []
        buy_signals = []
        sell_signals = []

        # D-1, D-2 캔들 초기화
        i = 0  # 인덱스 초기화
        d_1 = None
        d_2 = None
        d_3 = None 

        recent_buy_prices = {
            'price' : 0,
            'timestamp' : None
        }  # 최근 매수가격 기록
        
        while i < len(ohlc_data):

            candle = ohlc_data[i]
            open_price = float(candle.open)
            high_price = float(candle.high)
            low_price = float(candle.low)
            close_price = float(candle.close)
            volume = float(candle.volume)
            timestamp = candle.time
            timestamps.append(timestamp)
            closes.append(close_price) #rsi
            trade_reasons = logic.trade_reasons

            # timestamp 변수를 ISO 8601 문자열로 변환
            timestamp_iso = timestamp.isoformat()
            timestamp_str = timestamp.date().isoformat()
            
            ohlc.append([timestamp_str, open_price, high_price, low_price, close_price, volume])
            previous_closes.append(close_price)
            
            # 캔들 차트 데이터프레임 생성
            df = pd.DataFrame(ohlc, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'], index=pd.DatetimeIndex(timestamps))
            #ema
            df = indicator.cal_ema_df(df, 10)
            df = indicator.cal_ema_df(df, 20)
            df = indicator.cal_ema_df(df, 50)
            df = indicator.cal_ema_df(df, 60)
            
            #sma
            df = indicator.cal_sma_df(df, 5)
            df = indicator.cal_sma_df(df, 20)
            df = indicator.cal_sma_df(df, 40)
            df = indicator.cal_sma_df(df, 120)
            df = indicator.cal_sma_df(df, 200)

            df = indicator.cal_rsi_df(df, rsi_period)
            df = indicator.cal_macd_df(df)
            df = indicator.cal_stochastic_df(df)
            df = indicator.cal_mfi_df(df)
            
            trade_entry = {
                'symbol': symbol,
                'Time': timestamp,
                'price': close_price,
                'volume': volume,
                'rsi': df['rsi'].iloc[-1],
                'mfi': df['mfi'].iloc[-1],
                'macd': df['macd'].iloc[-1],
                'macd_signal': df['macd_signal'].iloc[-1],
                'macd_histogram': df['macd_histogram'].iloc[-1],
                'stochastic_k': df['stochastic_k'].iloc[-1],
                'stochastic_d': df['stochastic_d'].iloc[-1],
                'EMA_10': df['EMA_10'].iloc[-1],
                'EMA_20': df['EMA_20'].iloc[-1],
                'EMA_50': df['EMA_50'].iloc[-1],
                'EMA_60': df['EMA_60'].iloc[-1],
                'SMA_5' : df['SMA_5'].iloc[-1],
                'SMA_20' : df['SMA_20'].iloc[-1],
                'SMA_40' : df['SMA_40'].iloc[-1],                
            }
            trade_reasons.append(trade_entry)
                        
            recent_20_days_volume = []
            avg_volume_20_days = 0

            if len(ohlc_data[:i]) >= 21:
                recent_20_days_volume = [float(c.volume) for c in ohlc_data[i - 20:i]]
                avg_volume_20_days = sum(recent_20_days_volume) / len(recent_20_days_volume)
            
            sell_reason = None

            # 매수형 로직 처리
            if buy_trading_logic:
                for trading_logic in buy_trading_logic:
                    buy_yn = False # 각 로직에 대한 매수 신호 초기화
                    
                    if trading_logic == 'check_wick':            
                        # 볼린저 밴드 계산
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        buy_yn, _ = logic.check_wick(candle, previous_closes, symbol, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
                        
                    elif trading_logic == 'rsi_trading':            
                        buy_yn, _ = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)

                    elif trading_logic == 'penetrating':
                        buy_yn = logic.penetrating(candle, d_1, d_2, closes)

                    elif trading_logic == 'engulfing':
                        buy_yn = logic.engulfing(candle, d_1, d_2, closes)

                    elif trading_logic == 'engulfing2':
                        buy_yn = logic.engulfing2(candle, d_1, closes)

                    elif trading_logic == 'counterattack':
                        buy_yn = logic.counterattack(candle, d_1, d_2, closes)

                    elif trading_logic == 'doji_star':
                        buy_yn = logic.doji_star(candle, d_1, d_2, closes)

                    elif trading_logic == 'harami':
                        buy_yn = logic.harami(candle, d_1, d_2, closes)

                    elif trading_logic == 'morning_star':
                        buy_yn = logic.morning_star(candle, d_1, d_2, closes)
                        
                    elif trading_logic == 'macd_trading':
                        buy_yn, _ = logic.macd_trading(candle, df, symbol)
                                                
                    elif trading_logic == 'mfi_trading':
                        buy_yn, _ = logic.mfi_trading(df, symbol)    
                        
                    elif trading_logic == 'stochastic_trading':
                        buy_yn, _ = logic.stochastic_trading(df, symbol)
                        
                    elif trading_logic == 'rsi+mfi':
                        buy_yn1, _ = logic.mfi_trading(df)
                        buy_yn2, _ = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                        buy_yn = buy_yn1 and buy_yn2
                        
                    elif trading_logic == 'ema_breakout_trading':
                        buy_yn = logic.ema_breakout_trading(df, symbol)
                        
                    elif trading_logic == 'bollinger_band_trading':
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        buy_yn, _ = logic.bollinger_band_trading(bollinger_band['lower'], bollinger_band['upper'], df)
                        
                    elif trading_logic == 'bollinger+ema':
                        buy_yn1 = logic.ema_breakout_trading(df)
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        buy_yn2, _ = logic.bollinger_band_trading(bollinger_band['lower'], bollinger_band['upper'], df)                                                                        
                        buy_yn = buy_yn1 or buy_yn2
                        
                    elif trading_logic == 'ema_breakout_trading2':
                        buy_yn = logic.ema_breakout_trading2(df, symbol)
                        
                    elif trading_logic == 'trend_entry_trading':
                        buy_yn = logic.trend_entry_trading(df)
                        
                    elif trading_logic == 'bottom_rebound_trading':
                        buy_yn = logic.bottom_rebound_trading(df)
                        
                    elif trading_logic == 'sma_breakout_trading':
                        buy_yn = logic.sma_breakout_trading(df, symbol)
                        
                    elif trading_logic == 'ema_breakout_trading3':
                        buy_yn = logic.ema_breakout_trading3(df, symbol)                    
                    
                    # 매수, 전일 거래량이 전전일 거래량보다 크다는 조건 추가, #d_1.volume > avg_volume_20_days  
                    #if buy_yn and d_1 is not None and volume > d_1.volume and d_1.volume > avg_volume_20_days:
                    if buy_yn: # 일단 매수 거래량 조건 제거
                                                
                        can_buy = True
                        
                        # 매수 제한 조건 확인                        
                        if buy_percentage is not None:
                            #첫 매수는 항상 허용
                            if recent_buy_prices['price'] == 0:
                                can_buy = True
                            else:
                                price_range = recent_buy_prices['price'] * buy_percentage / 100
                                price_lower = recent_buy_prices['price'] - price_range
                                price_upper = recent_buy_prices['price'] + price_range
                                
                                # 최근 매수가격이 설정된 범위 내에 있으면 매수하지 않음
                                if price_lower <= close_price <= price_upper and timestamp_iso != recent_buy_prices['timestamp']:
                                    print(f"🚫 매수 조건 충족했지만, {buy_percentage}% 범위 내 기존 매수가 존재하여 매수하지 않음 ({close_price}KRW)")
                                    can_buy = False  # 매수를 막음
                        # ✅ 실제 투자 모드: 현금 확인 후 매수
                        if real_trading:
                            #현재 initial_capital을 기준으로 예수금 체크
                            if trading_history['initial_capital'] < close_price:
                                print(f"❌ 현금 부족으로 매수 불가 (잔액: {trading_history['initial_capital']:,.0f} KRW)")
                                can_buy = False
                                
                        if can_buy:
                            stop_loss_price = d_1.low if d_1 else None
                            float_stop_loss_price = float(stop_loss_price) if stop_loss_price else None
                            target_price = close_price + 2*(close_price - float_stop_loss_price) if float_stop_loss_price else None
                            
                        if real_trading:
                            # 매수 가능 최대 금액은 남은 initial_capital
                            max_affordable_amount = min(trade_amount, trading_history['initial_capital'])
                            buy_quantity = math.floor(max_affordable_amount / close_price)
                        else:
                            buy_quantity = math.floor(trade_amount / close_price)

                        if buy_quantity > 0:
                            total_trade_cost = buy_quantity * close_price

                            # 예수금 차감
                            if real_trading:
                                trading_history['initial_capital'] -= total_trade_cost

                            trading_history['history'].append({
                                'position': 'BUY',
                                'trading_logic': trading_logic,
                                'price': close_price,
                                'quantity': buy_quantity,
                                'target_price': target_price,
                                'stop_loss_price': float_stop_loss_price,
                                'time': timestamp_iso
                            })

                            buy_signals.append((timestamp, close_price))
                            recent_buy_prices.update({
                                'price' : close_price,
                                'timestamp' : timestamp_iso
                            
                            })
                            print(f"매수 시점: {timestamp_iso}, 매수가: {close_price} KRW, 매수량: {buy_quantity}, 손절가격: {stop_loss_price}, 익절 가격: {target_price}")        
            
                    # 손익 및 매매 횟수 계산
                    trading_history = self.calculate_pnl(trading_history, close_price)
                
            # 매도형 로직 처리
            if sell_trading_logic:
                for trading_logic in sell_trading_logic:
                    
                    sell_yn = False
                    #매도 시그널 로직: down_engulfing, down_engulfing2, down_counterattack, down_doji_star, down_harami, evening_star, dark_cloud
                    if trading_logic == 'down_engulfing':
                        sell_yn = logic.down_engulfing(candle, d_1, d_2)

                    elif trading_logic == 'down_engulfing2':
                        sell_yn = logic.down_engulfing2(candle, d_1)

                    elif trading_logic == 'down_counterattack':
                        sell_yn = logic.down_counterattack(candle, d_1, d_2)

                    elif trading_logic == 'down_doji_star':
                        sell_yn = logic.down_doji_star(candle, d_1, d_2)

                    elif trading_logic == 'down_harami':
                        sell_yn = logic.down_harami(candle, d_1, d_2)

                    elif trading_logic == 'evening_star':
                        sell_yn = logic.evening_star(candle, d_1, d_2)

                    elif trading_logic == 'dark_cloud':
                        sell_yn = logic.dark_cloud(candle, d_1, d_2)
                        
                    elif trading_logic == 'rsi_trading':
                        _, sell_yn = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                        
                    elif trading_logic == 'rsi_trading2':
                        _, sell_yn = logic.rsi_trading2(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                        
                    elif trading_logic == 'check_wick':            
                        # 볼린저 밴드 계산
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        _, sell_yn = logic.check_wick(candle, previous_closes, symbol, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
                        
                    elif trading_logic == 'mfi_trading':
                        _, sell_yn = logic.mfi_trading(df, symbol)
                        
                    elif trading_logic == 'stochastic_trading':
                        _, sell_yn = logic.stochastic_trading(df, symbol)
                        
                    elif trading_logic == 'macd_trading':
                        _, sell_yn = logic.macd_trading(candle, df, symbol)
                        
                    elif trading_logic == 'rsi+mfi':
                        _, sell_yn1 = logic.mfi_trading(df)
                        _, sell_yn2 = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                        sell_yn = sell_yn1 and sell_yn2
                        
                    elif trading_logic == 'bollinger_band_trading':
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        _, sell_yn = logic.bollinger_band_trading(bollinger_band['lower'], bollinger_band['upper'], df)
                        
                    elif trading_logic == 'top_reversal_sell_trading':
                        sell_yn = logic.top_reversal_sell_trading(df)
                        
                    elif trading_logic == 'downtrend_sell_trading':
                        sell_yn = logic.downtrend_sell_trading(df)
                #매도 사인이 2개 이상일 때 quantity 조건에 충족되지 않은 조건은 history에 추가되지 않는다는 문제 해결 필요
                # 매도
                if sell_yn:
                    if trading_history['total_quantity'] > 0:
                        # 매도 수량 계산
                        sell_quantity = (
                            trading_history['total_quantity']  # 보유 수량 이하로만 매도
                            if trading_history['total_quantity'] < math.floor(trade_amount / close_price)
                            else math.floor(trade_amount / close_price)
                        )

                        if sell_quantity > 0:
                            # 실현 손익 계산
                            realized_pnl = (close_price - trading_history['average_price']) * sell_quantity
                            total_sale_amount = close_price * sell_quantity

                            if real_trading:
                            # ✅ initial_capital 증가
                                trading_history['initial_capital'] += total_sale_amount

                            # 거래 내역 기록
                            trading_history['history'].append({
                                'position': 'SELL',
                                'trading_logic': trading_logic,
                                'price': close_price,
                                'quantity': sell_quantity,
                                'time': timestamp_iso,
                                'realized_pnl': realized_pnl
                            })

                            sell_signals.append((timestamp, close_price))
                            print(f"📉 매도 시점: {timestamp_iso}, 매도가: {close_price} KRW, 매도량: {sell_quantity}, 매도금액: {total_sale_amount:,.0f} KRW")
                        else:
                            print("⚠️ 매도 수량이 0이라서 거래 내역에 추가하지 않음")
                                
                    
                    # 손익 및 매매 횟수 계산
                    trading_history = self.calculate_pnl(trading_history, close_price)

            print(f"총 비용: {trading_history['total_cost']}KRW, 총 보유량: {trading_history['total_quantity']}주, 평균 단가: {trading_history['average_price']}KRW, "
                f"실현 손익 (Realized PnL): {trading_history['realized_pnl']}KRW, 미실현 손익 (Unrealized PnL): {trading_history['unrealized_pnl']}KRW")
            
            # D-2, D-1 업데이트
            d_3 = d_2
            d_2 = d_1
            d_1 = candle
            i += 1

        # 캔들 차트 데이터프레임 생성
        result_data = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)
        # print(f"result_data : {result_data}")
        # 매매 내역 요약 출력
        print("\n=== 매매 요약 ===")
        print(f"총 매수 횟수: {trading_history['buy_count']}")
        print(f"총 매도 횟수: {trading_history['sell_count']}")
        print(f"매수 날짜: {trading_history['buy_dates']}")
        print(f"매도 날짜: {trading_history['sell_dates']}")
        print(f"총 실현손익: {trading_history['realized_pnl']}KRW")
        print(f"미실현 손익 (Unrealized PnL): {trading_history['unrealized_pnl']}KRW")
        print(f"실현 손익률 (realized_roi): {trading_history['realized_roi']}%")
        print(f"총 실현 손익률 (unrealized_roi): {trading_history['unrealized_roi']}%")
        
        return result_data, trading_history, trade_reasons

    def whole_simulate_trading2(
        self, symbol, end_date, df, ohlc_data, trade_ratio,
        target_trade_value_krw, buy_trading_logic=None, sell_trading_logic=None,
        interval='day', buy_percentage=None,
        initial_capital=None, rsi_buy_threshold=30, rsi_sell_threshold=70,
        global_state=None, holding_state=None,use_take_profit=False, take_profit_ratio=5.0,
        use_stop_loss=False, stop_loss_ratio=5.0):
        
        df = df[df.index <= pd.Timestamp(end_date)]
        
        # ✅ 아무 데이터도 없으면 조용히 빠져나가기
        if df.empty or len(df) < 2:
            return None

        candle_time = df.index[-1]
        candle = next(c for c in ohlc_data if pd.Timestamp(c.time).tz_localize(None) == candle_time)
        close_price = float(candle.close)
        timestamp_str = candle_time.date().isoformat()
        

        # ✅ 상태 초기화
        trading_history = global_state.copy() if global_state else {}
        trading_history.setdefault('initial_capital', initial_capital)
        trading_history.setdefault('realized_pnl', 0)
        trading_history.setdefault('buy_dates', [])
        trading_history.setdefault('sell_dates', [])

        print(f"💰 시뮬 중: {symbol} / 날짜: {timestamp_str} / 사용 자본: {trading_history['initial_capital']:,}")
        
        state = holding_state.copy() if holding_state else {}
        state.setdefault('total_quantity', 0)
        state.setdefault('average_price', 0)
        state.setdefault('total_cost', 0)
        state.setdefault('buy_count', 0)
        state.setdefault('sell_count', 0)
        state.setdefault('buy_dates', [])
        state.setdefault('sell_dates', [])

        total_quantity = state['total_quantity']
        avg_price = state['average_price']
        total_cost = state['total_cost']

        buy_count = 0
        sell_count = 0
        trade_quantity = 0
        realized_pnl = None
        sell_signal = False
        buy_signal = False
        signal_reasons = []
        
        
        #익절, 손절
        take_profit_hit = False
        stop_loss_hit = False
        sell_triggered = False
        
        # ✅ 익절/손절 조건 우선 적용
        if total_quantity > 0:
            current_roi = ((close_price - avg_price) / avg_price) * 100

            if use_take_profit and current_roi >= take_profit_ratio:
                # 실제 매도 조건 충족
                revenue = total_quantity * close_price
                realized_pnl = revenue - (avg_price * total_quantity)
                trading_history['initial_capital'] += revenue

                total_quantity = 0
                total_cost = 0
                avg_price = 0
                sell_count = 1
                trade_quantity = total_quantity
                trading_history['sell_dates'].append(timestamp_str)

                take_profit_hit = True
                sell_signal = True
                reason = f"익절 조건 충족 (+{current_roi:.2f}%)"
                signal_reasons.append(reason)

            elif use_stop_loss and current_roi <= -stop_loss_ratio:
                # 실제 손절 조건 충족
                revenue = total_quantity * close_price
                realized_pnl = revenue - (avg_price * total_quantity)
                trading_history['initial_capital'] += revenue

                total_quantity = 0
                total_cost = 0
                avg_price = 0
                sell_count = 1
                trade_quantity = total_quantity
                trading_history['sell_dates'].append(timestamp_str)

                stop_loss_hit = True
                sell_signal = True
                reason = f"손절 조건 충족 ({current_roi:.2f}%)"
                signal_reasons.append(reason)

        
        # ✅ 매도 조건
        if not sell_signal:
            for logic_name in (sell_trading_logic or []):
                sell_yn = False
                if logic_name == 'rsi_trading':
                    _, sell_yn = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                    
                elif logic_name == 'rsi_trading2':
                    _, sell_yn = logic.rsi_trading2(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)

                if sell_yn:
                    sell_signal = True
                    signal_reasons.append(logic_name)
                    
            if sell_signal and total_quantity > 0:
                revenue = total_quantity * close_price
                realized_pnl = revenue - (avg_price * total_quantity)
                trading_history['initial_capital'] += revenue

                total_quantity = 0
                total_cost = 0
                avg_price = 0

                sell_count = 1
                trade_quantity = total_quantity
                trading_history['sell_dates'].append(timestamp_str)
                state['sell_dates'].append(timestamp_str)

        
        average_price = state["average_price"]
        # ✅ 평가 자산 기반 거래 금액 계산
        stock_value = total_quantity * close_price
        portfolio_value = trading_history['initial_capital'] + stock_value
        
        # ✅ 직접 지정된 target_trade_value_krw가 있으면 사용, 없으면 비율로 계산
        if target_trade_value_krw and target_trade_value_krw > 0:
            trade_amount = min(target_trade_value_krw, trading_history['initial_capital'])
        else:
            trade_ratio = trade_ratio if trade_ratio is not None else 100
            trade_amount = min(portfolio_value * (trade_ratio / 100), trading_history['initial_capital'])
        
        # ✅ 매수 조건
        for logic_name in (buy_trading_logic or []):
            buy_yn = False
            if logic_name == 'rsi_trading':
                buy_yn, _ = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                
            elif logic_name == 'ema_breakout_trading2':
                buy_yn = logic.ema_breakout_trading2(df, symbol)
                    
            elif logic_name == 'trend_entry_trading':
                buy_yn = logic.trend_entry_trading(df)
                
            elif logic_name == 'bottom_rebound_trading':
                buy_yn = logic.bottom_rebound_trading(df)
                
            elif logic_name == 'sma_breakout_trading':
                buy_yn = logic.sma_breakout_trading(df, symbol)
                
            elif logic_name == 'ema_breakout_trading':
                buy_yn = logic.ema_breakout_trading(df, symbol)
                
            elif logic_name == 'ema_breakout_trading3':
                buy_yn = logic.ema_breakout_trading3(df, symbol)                


            if buy_yn:
                buy_signal = True
                signal_reasons.append(logic_name)
                
                #amount = min(target_trade_value_krw, trading_history['initial_capital'])
                buy_qty = math.floor(trade_amount / close_price)

                if buy_qty > 0:
                    cost = buy_qty * close_price
                    trading_history['initial_capital'] -= cost

                    total_cost += cost
                    total_quantity += buy_qty
                    avg_price = total_cost / total_quantity

                    buy_count = 1
                    trade_quantity = buy_qty
                    trading_history['buy_dates'].append(timestamp_str)
                    state['buy_dates'].append(timestamp_str)

        # ✅ 손익 계산
        unrealized_pnl = (close_price - avg_price) * total_quantity if total_quantity > 0 else 0
        unrealized_roi = (unrealized_pnl / total_cost) * 100 if total_cost > 0 else 0
        realized_roi = (realized_pnl / total_cost) * 100 if realized_pnl and total_cost > 0 else 0

        # ✅ 상태 업데이트
        state.update({
            'total_quantity': total_quantity,
            'average_price': avg_price,
            'total_cost': total_cost,
            'buy_count': buy_count,
            'sell_count': sell_count,
        })
        holding_state.update(state)

        return {
            'symbol': symbol,
            'sim_date': timestamp_str,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'quantity': trade_quantity,
            'realized_pnl': realized_pnl,
            'realized_roi': realized_roi,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_roi': unrealized_roi,
            'average_price': avg_price,
            'total_quantity': total_quantity,
            'initial_capital': trading_history['initial_capital'],
            'buy_dates': trading_history['buy_dates'],
            'sell_dates': trading_history['sell_dates'],
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'signal_reasons': signal_reasons,
            'take_profit_hit': take_profit_hit,
            'stop_loss_hit': stop_loss_hit,
            "portfolio_value": portfolio_value
        }
    
    def save_trading_history_to_db_with_executor(self, trading_history, symbol):
        """
        trading_history 데이터를 DB에 저장하는 함수 (sql_executor 사용)
        
        Parameters:
        - trading_history: dict, 저장할 거래 데이터
        - symbol: str, 종목 코드
        - sql_executor: SQLExecutor 객체
        """

        dynamodb_executor = DynamoDBExecutor()
        # 한국 시간대
        kst = timezone("Asia/Seoul")
        # 현재 시간을 KST로 변환
        current_time = datetime.now(kst)
        created_at = int(current_time.timestamp() * 1000)  # ✅ 밀리세컨드 단위로 SK 생성

        data_model = SimulationHistory(
            symbol=symbol,
            created_at=created_at,
            updated_at=None,
            average_price=trading_history['average_price'],
            realized_pnl=trading_history['realized_pnl'],
            unrealized_pnl=trading_history['unrealized_pnl'],
            realized_roi=trading_history['realized_roi'],
            unrealized_roi=trading_history['unrealized_roi'],
            total_cost=trading_history['total_cost'],
            total_quantity=trading_history['total_quantity'],
            buy_count=trading_history['buy_count'],
            sell_count=trading_history['sell_count'],
            buy_dates=trading_history['buy_dates'],
            sell_dates=trading_history['sell_dates'],
            history=json.dumps(trading_history["history"])
        )

        result = dynamodb_executor.execute_save(data_model)
        print(f"Trading history for {symbol} saved successfully: {result}")
        return result
    

    # 실시간 매매 함수
    def trade(self, trading_bot_name, buy_trading_logic, sell_trading_logic, symbol, symbol_name, start_date, end_date, target_trade_value_krw, interval='day', max_allocation = 0.01,  take_profit_threshold: float = 5.0,   # 퍼센트 단위
    stop_loss_threshold: float = 1.0, use_take_profit: bool = True, use_stop_loss: bool = True):
        #buy_trading_logic, sell_trading_logic => list
        
        ohlc_data = self._get_ohlc(symbol, start_date, end_date, interval)

        # OHLC 데이터 전체를 기반으로 DataFrame 구성
        timestamps = [candle.time for candle in ohlc_data]
        ohlc = [
            [candle.time, float(candle.open), float(candle.high), float(candle.low), float(candle.close), float(candle.volume)]
            for candle in ohlc_data
        ]

        # 캔들 차트 데이터프레임 생성
        df = pd.DataFrame(ohlc, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'], index=pd.DatetimeIndex(timestamps))

        # 지표 계산 (전체 df에 대해)
        df = indicator.cal_ema_df(df, 10)
        df = indicator.cal_ema_df(df, 20)
        df = indicator.cal_ema_df(df, 50)
        df = indicator.cal_ema_df(df, 60)
        df = indicator.cal_rsi_df(df)
        df = indicator.cal_macd_df(df)
        df = indicator.cal_stochastic_df(df)
        df = indicator.cal_mfi_df(df)
    
        #sma
        df = indicator.cal_sma_df(df, 5)
        df = indicator.cal_sma_df(df, 20)
        df = indicator.cal_sma_df(df, 40)
        
        # 볼린저 밴드 계산용 종가 리스트
        close_prices = df['Close'].tolist()
        bollinger_band = indicator.cal_bollinger_band(close_prices[:-1], close_prices[-1])
        
        # 마지막 봉 기준 데이터 추출
        candle = ohlc_data[-1]
        candle_time = candle.time
        last = df.iloc[-1]
        prev = df.iloc[-2]

        close_price = float(last['Close'])
        prev_price = float(prev['Close'])
        close_open_price = float(last['Open'])
        volume = float(last['Volume'])
        previous_closes = df['Close'].iloc[:-1].tolist()

        recent_20_days_volume = []
        avg_volume_20_days = 0

        if len(ohlc_data) >= 21:
            recent_20_days_volume = [float(c.volume) for c in ohlc_data[-20:]]
            avg_volume_20_days = sum(recent_20_days_volume) / len(recent_20_days_volume)
            
        for trading_logic in buy_trading_logic:
            buy_yn = False # 각 로직에 대한 매수 신호 초기화

            if trading_logic == 'check_wick':            
                buy_yn, _ = logic.check_wick(candle, previous_closes, symbol,
                                            bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
            elif trading_logic == 'rsi_trading':
                buy_yn, _ = logic.rsi_trading(candle, df['rsi'], symbol)
            elif trading_logic == 'mfi_trading':
                buy_yn, _ = logic.mfi_trading(df, symbol)
            elif trading_logic == 'stochastic_trading':
                buy_yn, _ = logic.stochastic_trading(df, symbol)
            elif trading_logic == 'ema_breakout_trading2':
                buy_yn = logic.ema_breakout_trading2(df, symbol)    
            elif trading_logic == 'trend_entry_trading':
                buy_yn = logic.trend_entry_trading(df)
            elif trading_logic == 'bottom_rebound_trading':
                buy_yn = logic.bottom_rebound_trading(df)
            elif trading_logic == 'ema_breakout_trading':
                buy_yn = logic.ema_breakout_trading(df, symbol)
            elif trading_logic == 'sma_breakout_trading':
                buy_yn = logic.sma_breakout_trading(df, symbol)
            elif trading_logic == 'bollinger_band_trading':
                bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                buy_yn, _ = logic.bollinger_band_trading(bollinger_band['lower'], bollinger_band['upper'], df)
            elif trading_logic == 'macd_trading':
                buy_yn, _ = logic.macd_trading(candle, df, symbol)    
            
            if buy_yn:
                reason = trading_logic    
                self.send_discord_webhook(f"[reason:{reason}], {symbol_name} 매도가 완료되었습니다. 매도금액 : {int(ohlc_data[-1].close)}KRW", "trading")


            self._trade_kis(
                buy_yn=buy_yn,
                sell_yn=False,
                volume=volume,
                prev=prev,
                avg_volume_20_days=avg_volume_20_days,
                trading_logic=trading_logic,
                symbol=symbol,
                symbol_name=symbol_name,
                ohlc_data=ohlc_data,
                trading_bot_name=trading_bot_name,
                target_trade_value_krw=target_trade_value_krw,
                max_allocation = max_allocation
            )
            
        # 🟡 trade 함수 상단
        account = self.kis.account()
        balance: KisBalance = account.balance()

        for trading_logic in sell_trading_logic:
            sell_yn = False

            # 기존 매도 로직
            if trading_logic == 'check_wick':
                _, sell_yn = logic.check_wick(candle, previous_closes, symbol, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
            elif trading_logic == 'rsi_trading':
                _, sell_yn = logic.rsi_trading(candle, df['rsi'], symbol)
            elif trading_logic == 'mfi_trading':
                _, sell_yn = logic.mfi_trading(df, symbol)
            elif trading_logic == 'top_reversal_sell_trading':
                sell_yn = logic.top_reversal_sell_trading(df)
            elif trading_logic == 'downtrend_sell_trading':
                sell_yn = logic.downtrend_sell_trading(df)
            elif trading_logic == 'stochastic_trading':
                _, sell_yn = logic.stochastic_trading(df, symbol)
            elif trading_logic == 'bollinger_band_trading':
                bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                _, sell_yn = logic.bollinger_band_trading(bollinger_band['lower'], bollinger_band['upper'], df)
            elif trading_logic == 'macd_trading':
                _, sell_yn = logic.macd_trading(candle, df, symbol)

            # ✅ 익절/손절 조건 확인
            take_profit_hit = False
            stop_loss_hit = False
            
            holding = next((stock for stock in balance.stocks if stock.symbol == symbol), None)

            if holding:
                profit_rate = float(holding.profit_rate)

                if use_take_profit and profit_rate >= take_profit_threshold:
                    take_profit_hit = True

                if use_stop_loss and profit_rate <= -stop_loss_threshold:
                    stop_loss_hit = True

            # 최종 매도 조건
            final_sell_yn = sell_yn or take_profit_hit or stop_loss_hit

            if final_sell_yn:
                if sell_yn:
                    reason = trading_logic
                elif take_profit_hit:
                    reason = "익절"
                elif stop_loss_hit:
                    reason = "손절"
                self.send_discord_webhook(f"[reason:{reason}], {symbol_name} 매도가 완료되었습니다. 매도금액 : {int(ohlc_data[-1].close)}KRW", "trading")

                print(f"✅ 매도 조건 충족: {symbol_name} - 매도 사유: {reason}")

            self._trade_kis(
                buy_yn=False,
                sell_yn=final_sell_yn,
                volume=volume,
                prev=prev,
                avg_volume_20_days=avg_volume_20_days,
                trading_logic=trading_logic,
                symbol=symbol,
                symbol_name=symbol_name,
                ohlc_data=ohlc_data,
                trading_bot_name=trading_bot_name,
                target_trade_value_krw=target_trade_value_krw,
                max_allocation=max_allocation
            )

        # 마지막 직전 봉 음봉, 양봉 계산
        is_bearish_prev_candle = close_price < close_open_price  # 음봉 확인
        is_bullish_prev_candle = close_price > close_open_price  # 양봉 확인

        print(f'마지막 직전 봉 : {close_price - close_open_price}. 양봉 : {is_bullish_prev_candle}, 음봉 : {is_bearish_prev_candle}')

        return None
    

    def _trade_kis(self, buy_yn, sell_yn, volume, prev, avg_volume_20_days, trading_logic, symbol, symbol_name, ohlc_data, trading_bot_name, target_trade_value_krw, max_allocation):

        if buy_yn:
            order_type = 'buy'
            # 매수 주문은 특정 로직에서만 실행
            if trading_logic == 'ema_breakout_trading2':
                self._trade_place_order(symbol, symbol_name, target_trade_value_krw, order_type, max_allocation, trading_bot_name)

            position = 'BUY'
            quantity = 1  # 임시
            
            self._insert_trading_history(
                trading_logic, position, trading_bot_name, ohlc_data[-1].close, 
                quantity, symbol, symbol_name
            )
        
        if sell_yn:
            order_type = 'sell'
            # 매도 주문은 특정 로직에서만 실행
            if trading_logic == 'rsi_trading':
                self._trade_place_order(symbol, symbol_name, target_trade_value_krw, order_type, max_allocation, trading_bot_name)
                
                # trade history 에 추가
                position = 'SELL'
                quantity = 1 # 임시

                self._insert_trading_history(trading_logic, position, trading_bot_name, ohlc_data[-1].close,
                    quantity, symbol, symbol_name
                )


    def _insert_trading_history(self, trading_logic, position, trading_bot_name, price, quantity, symbol, symbol_name, data_type='test'):
        
        dynamodb_executor = DynamoDBExecutor()
        # 한국 시간대
        kst = timezone("Asia/Seoul")
        # 현재 시간을 KST로 변환
        current_time = datetime.now(kst)
        created_at = int(current_time.timestamp() * 1000)  # ✅ 밀리세컨드 단위로 SK 생성

        data_model = TradingHistory(
            trading_bot_name=trading_bot_name,
            created_at=created_at,
            updated_at=None,
            trading_logic=trading_logic,
            trade_date=created_at,
            symbol=symbol,
            symbol_name=symbol_name,
            position=position,
            price=float(price),
            quantity=float(quantity),
            data_type=data_type
        )

        result = dynamodb_executor.execute_save(data_model)
        print(f'execute_save 결과 = {result}')

        return result
    
    def _insert_auto_trading(self, trading_bot_name,trading_logic,symbol,symbol_name,position,price,quantity):
        # 한국 시간대 기준 timestamp
        kst = timezone("Asia/Seoul")
        now = datetime.now(kst)
        created_at = int(now.timestamp() * 1000)
        trade_date = int(now.strftime("%Y%m%d"))

        data_model = AutoTrading(
            trading_bot_name=trading_bot_name,
            created_at=created_at,
            updated_at=None,
            trading_logic=trading_logic,
            trade_date=trade_date,
            symbol=symbol,
            symbol_name=symbol_name,
            position=position,
            price=float(price),
            quantity=float(quantity)
        )

        dynamodb_executor = DynamoDBExecutor()
        result = dynamodb_executor.execute_save(data_model)
        print(f'[자동매매 로그 저장] execute_save 결과 = {result}')

    def _upsert_account_balance(self, trading_bot_name):
        kst = timezone("Asia/Seoul")
        updated_at = int(datetime.now(kst).timestamp() * 1000)

        holdings = self.get_holdings_with_details()
        
        dynamodb_executor = DynamoDBExecutor()
    
        # ✅ 3. 기존 잔고 모두 삭제
        existing_items = AutoTradingBalance.query(trading_bot_name)
        for item in existing_items:
            try:
                item.delete()
                print(f'🗑️ 삭제된 종목: {item.symbol}')
            except Exception as e:
                print(f'❌ 삭제 실패 ({item.symbol}): {e}')

        # ✅ 4. 현재 잔고 다시 저장
        for holding in holdings:
            try:
                model = AutoTradingBalance(
                    trading_bot_name=trading_bot_name,
                    symbol=holding['symbol'],
                    updated_at=updated_at,
                    symbol_name=holding['symbol_name'],
                    market=holding['market'],
                    quantity=holding['quantity'],
                    avg_price=holding['price'],
                    amount=holding['amount'],
                    profit=holding['profit'],
                    profit_rate=holding['profit_rate'],
                )

                dynamodb_executor.execute_save(model)
                print(f'[💾 잔고 저장] {holding["symbol"]}')

            except Exception as e:
                print(f"❌ 잔고 저장 실패 ({holding['symbol_name']}): {e}")
    
    def place_order(self, symbol, symbol_name, qty, order_type, buy_price=None, sell_price=None, deposit = None, trading_bot_name = 'schedulerbot'):
        """주식 매수/매도 주문 함수
        Args:
            deposit : 예수금
            symbol (str): 종목 코드
            qty (int): 주문 수량
            price (int, optional): 주문 가격. 지정가 주문 시 필요
            order_type (str): "buy" 또는 "sell"
        """
        try:
            # 종목 객체 가져오기
            stock = self.kis.stock(symbol)

            # 매수/매도 주문 처리
            if order_type == "buy":
                if buy_price:
                    order = stock.buy(price=buy_price, qty=qty)  # price 값이 있으면 지정가 매수
                else:
                    order = stock.buy(qty=qty)  # 시장가 매수
                message = f"📈 매수 주문 완료! bot: {trading_bot_name} 종목: {symbol}, 종목명: {symbol_name} 수량: {qty}, 가격: {'시장가' if not buy_price else buy_price}"
            elif order_type == "sell":
                if sell_price:
                    order = stock.sell(price=sell_price)  # 지정가 매도
                else:
                    order = stock.sell()  # 시장가 매도
                message = f"📉 매도 주문 완료! bot: {trading_bot_name} 종목: {symbol}, 종목명: {symbol_name} 수량: {qty}, 가격: {'시장가' if not sell_price else sell_price}"
            else:
                raise ValueError("Invalid order_type. Must be 'buy' or 'sell'.")

            # 디스코드로 주문 결과 전송
            self.send_discord_webhook(message, "trading")

            return order
        
        except Exception as e:
            error_message = f"주문 처리 중 오류 발생: {e}\n 예수금 : {deposit}, "
            print(error_message)
            self.send_discord_webhook(error_message, "trading")



    def _get_quote(self, symbol):
        quote: KisQuote = self.kis.stock(symbol).quote()
        return quote


    def _trade_place_order(self, symbol, symbol_name, target_trade_value_krw, order_type, max_allocation, trading_bot_name):
        quote = self._get_quote(symbol=symbol)
        buy_price = None  # 시장가 매수
        sell_price = None # 시장가 매도

        if order_type == 'buy':
            qty = math.floor(target_trade_value_krw / quote.close)
            
            if qty <= 0:
                print(f"[{datetime.now()}] 🚫 수량이 0입니다. 매수 생략: {symbol}")
                return

            # ✅ 예수금 조회 (inquire_balance() 사용)
            deposit = self.inquire_balance()
            order_amount = qty * quote.close
            buying_limit = deposit * Decimal(str(max_allocation))
            
        
            if order_amount > buying_limit:
                print(f"[{datetime.now()}] 🚫 매수 생략: 주문금액 {order_amount:,}원이 예수금의 {max_allocation*100:.0f}% 초과")
                message = f"[{datetime.now()}] 🚫 매수 생략: 주문금액 {order_amount:,}원이 예수금의 {max_allocation*100:.0f}% 초과"
                return

            print(f"[{datetime.now()}] ✅ 자동 매수 실행: bot: {trading_bot_name} 종목 {symbol_name}, 수량 {qty}주, 주문 금액 {order_amount:,}원")
            message = f"[{datetime.now()}] ✅ 자동 매수 실행: bot: {trading_bot_name} 종목 {symbol_name}, 수량 {qty}주, 주문 금액 {order_amount:,}원"
            try:
                self.place_order(
                    deposit=deposit,
                    symbol=symbol,
                    symbol_name = symbol_name,
                    qty=qty,
                    order_type="buy",
                    buy_price=buy_price,
                    trading_bot_name = trading_bot_name
                )
            except Exception as e:
                print(f"[{datetime.now()}] ❌ 매수 실패: {e}")
            
        elif order_type == 'sell':
            # ✅ 보유 종목에서 해당 symbol 찾아서 수량 확인
            holdings = self.get_holdings()
            holding = next((item for item in holdings if item[0] == symbol), None) #holding => 튜플

            if not holding:
                print(f"[{datetime.now()}] 🚫 매도 생략: {symbol} 보유 수량 없음")
                return

            qty = holding[1] #수량을 저장, holding[0]은 종목 코드

            print(f"[{datetime.now()}] ✅ 자동 매도 실행: bot: {trading_bot_name} 종목 {symbol_name}, 수량 {qty}주 (시장가 매도)")
            message = f"[{datetime.now()}] ✅ 자동 매도 실행: bot: {trading_bot_name} 종목 {symbol_name}, 수량 {qty}주 (시장가 매도)"
            try:
                self.place_order(
                    symbol=symbol,
                    symbol_name = symbol_name,
                    qty=qty,
                    order_type='sell',
                    sell_price=sell_price,
                    trading_bot_name = trading_bot_name
                )
                
            except Exception as e:
                print(f"[{datetime.now()}] ❌ 매도 실패: {e}")

        else:
            print(f"[{datetime.now()}] ❌ 잘못된 주문 타입입니다: {order_type}")
            
        self.send_discord_webhook(message, "trading")
            
    def inquire_balance(self):
        """잔고 정보를 디스코드 웹훅으로 전송"""
        
                # 주 계좌 객체를 가져옵니다.
        account = self.kis.account()

        balance: KisBalance = account.balance()
        
        try:
            # 기본 잔고 정보
            message = (
                f"📃 주식 잔고 정보\n"
                f"계좌 번호: {balance.account_number}\n"
                f"총 구매 금액: {balance.purchase_amount:,.0f} KRW\n"
                f"현재 평가 금액: {balance.current_amount:,.0f} KRW\n"
                f"총 평가 손익: {balance.profit:,.0f} KRW\n"
                f"총 수익률: {balance.profit_rate/ 100:.2%}\n\n"
            )
            
            
            # 보유 종목 정보 추가
            message += "📊 보유 종목 정보:\n"
            for stock in balance.stocks:
                message += (
                    f"종목명: {stock.symbol} (시장: {stock.market})\n"
                    f"수량: {stock.qty:,}주\n"
                    f"평균 단가: {stock.price:,.0f} KRW\n"
                    f"평가 금액: {stock.amount:,.0f} KRW\n"
                    f"평가 손익: {stock.profit:,.0f} KRW\n"
                    f"수익률: {stock.profit_rate /100:.2%}\n\n"
                )
                
            
            
            # 예수금 정보 추가
            message += "💰 예수금 정보:\n"
            for currency, deposit in balance.deposits.items():
                message += (
                    f"통화: {currency}\n"
                    f"금액: {deposit.amount:,.0f} {currency}\n"
                    f"환율: {deposit.exchange_rate}\n\n"
                )

            # 디스코드 웹훅으로 메시지 전송
            #self.send_discord_webhook(message, "alarm")

        except Exception as e:
            # 오류 메시지 처리
            error_message = f"❌ 잔고 정보를 처리하는 중 오류 발생: {e}"
            print(error_message)
            return None
            #self.send_discord_webhook(error_message, "alarm")

        return deposit.amount

    def get_holdings(self):
        """보유 종목의 (symbol, qty) 튜플 리스트 반환"""
        account = self.kis.account()
        balance = account.balance()

        holdings = [
            (stock.symbol, stock.qty)
            for stock in balance.stocks
            if stock.qty > 0
        ]
        return holdings

    def get_holdings_with_details(self):

        account = self.kis.account()
        balance = account.balance()

        holdings = []
        for stock in balance.stocks:
            if stock.qty > 0:
                holding = {
                    'symbol': stock.symbol,
                    'symbol_name': stock.name,
                    'market': stock.market,
                    'quantity': int(stock.qty),
                    'price': int(stock.price),             # 평균 단가
                    'amount': int(stock.amount),           # 평가 금액
                    'profit': int(stock.profit),           # 평가 손익
                    'profit_rate': float(stock.profit_rate), # 수익률 (ex: 2.78)
                }
                holdings.append(holding)

        return holdings

    # 컷 로스 (손절)
    def cut_loss(self, target_trade_value_usdt):
        pass