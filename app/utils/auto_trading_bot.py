import datetime
import numpy as np
import pandas as pd
import requests
import math
import json
from pykis import PyKis, KisChart, KisStock
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
from app.utils.dynamodb.model.user_info_model import UserInfo


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

        # MA 계산
        df['SMA_60'] = np.nan
        df['SMA_120'] = np.nan
        df['SMA_200'] = np.nan

        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_60'] = df['Close'].rolling(window=60).mean()
        df['SMA_120'] = df['Close'].rolling(window=120).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        #ema
        df = indicator.cal_ema_df(df, 5)
        df = indicator.cal_ema_df(df, 60)
        df = indicator.cal_ema_df(df, 120)
        df = indicator.cal_ema_df(df, 200)

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

        # MA 를 그릴 수 있는 경우에만
        if df['SMA_60'].notna().any():
            add_plot.append(mpf.make_addplot(df['SMA_60'], color='red', linestyle='-', label='SMA 60'))
        if df['SMA_120'].notna().any():
            add_plot.append(mpf.make_addplot(df['SMA_120'], color='purple', linestyle='-', label='SMA 120'))
        if df['SMA_200'].notna().any():
            add_plot.append(mpf.make_addplot(df['SMA_200'], color='gray', linestyle='-', label='SMA 200'))

        # signal이 존재할 때만 가능
        if len(buy_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Buy_Signal'], type='scatter', markersize=60, marker='^', color='black', label='BUY'))
        if len(sell_signals) > 0:
            add_plot.append(mpf.make_addplot(df['Sell_Signal'], type='scatter', markersize=60, marker='v', color='black', label='SELL'))

        #simulation_plot = mpf.plot(df, type='candle', style='charles', title=f'{symbol}', addplot=add_plot, volume=True, ylabel_lower='Volume', ylabel='Price(KRW)', figsize=(20, 9), returnfig=True)

        return df


    def calculate_pnl(self, trading_history, current_price, initial_capital):
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
                if initial_capital is not None:
                    initial_capital-= buy_price * buy_quantity
                
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
                
                #초기 자본 증가
                if initial_capital is not None:
                    initial_capital +=sell_price * sell_quantity
            
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
            'initial_capital': initial_capital
        })
        
        print(f"투자비용: {investment_cost}")
        return trading_history
    

    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw, buy_trading_logic=None, sell_trading_logic=None,
                        interval='day', buy_percentage = None, ohlc_mode = 'default',rsi_buy_threshold = 35, rsi_sell_threshold = 70, initial_capital=None):
        
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
            print(f"df: {df}")  
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
                        df = indicator.cal_rsi_df(df, 14)
                        
                        # ✅ df 출력 (여기서 실제 전달되는 값 확인)
                        print("\n✅ RSI 계산 후 df:")
                        print(df.tail(10))  # 최근 10개만 출력
                        
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
                        df = indicator.cal_macd_df(df)
                        buy_yn, _ = logic.macd_trading(candle, df)
                                                
                    elif trading_logic == 'mfi_trading':
                        df = indicator.cal_mfi_df(df)
                        buy_yn, _ = logic.mfi_trading(df)    
                    #rsi와 check_wick and 조건
                    elif trading_logic == 'rsi+check_wick':
                        # 볼린저 밴드 계산
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        _, buy_yn1 = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
                        rsi_values = indicator.cal_rsi(closes, 14)
                        buy_yn2, _ = logic.rsi_trading(rsi_values, rsi_buy_threshold, rsi_sell_threshold)
                        buy_yn = buy_yn1 and buy_yn2
                        
                    elif trading_logic == 'stochastic_trading':
                        df = indicator.cal_stochastic_df(df, 14, 3)
                        print(f"스토캐스틱 계산 후 df: {df}")
                        buy_yn, _ = logic.stochastic_trading(df)
                        
                        
                        # 매수, 전일 거래량이 전전일 거래량보다 크다는 조건 추가, #d_1.volume > avg_volume_20_days  
                    #if buy_yn and volume > d_1.volume and d_1.volume > avg_volume_20_days:
                    if buy_yn and volume > d_1.volume:
                                                
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
                            if trading_history['initial_capital'] < close_price:
                                print(f"❌ 현금 부족으로 매수 불가 (잔액: {trading_history['initial_capital']:,.0f} KRW)")
                                can_buy = False
                                
                        if can_buy:
                            stop_loss_price = d_1.low if d_1 else None
                            float_stop_loss_price = float(stop_loss_price)
                            target_price = close_price + 2*(close_price - float_stop_loss_price) if float_stop_loss_price else None
                            if real_trading:
                                if trading_history['initial_capital'] > trade_amount:
                                    buy_quantity = math.floor(trade_amount / close_price)
                                else:
                                    buy_quantity = math.floor(trading_history['initial_capital'] / close_price)
                            else:
                                buy_quantity = math.floor(trade_amount / close_price)

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
                    trading_history = self.calculate_pnl(trading_history, close_price, trading_history['initial_capital'])
                
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
                        df = indicator.cal_rsi_df(df, 14)
                        #print(f"rsi 데이터: {df['rsi']}")
                        _, sell_yn = logic.rsi_trading(candle, df['rsi'], symbol, rsi_buy_threshold, rsi_sell_threshold)
                        
                    elif trading_logic == 'check_wick':            
                        # 볼린저 밴드 계산
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        _, sell_yn = logic.check_wick(candle, previous_closes, symbol, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
                        
                    elif trading_logic == 'mfi_trading':
                        df = indicator.cal_mfi_df(df)
                        _, sell_yn = logic.mfi_trading(df)
                        
                    #rsi와 check_wick and 조건
                    elif trading_logic == 'rsi+check_wick':
                        # 볼린저 밴드 계산
                        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
                        sell_yn1, _ = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
                        rsi_values = indicator.cal_rsi(closes, 14)
                        _, sell_yn2 = logic.rsi_trading(rsi_values, rsi_buy_threshold, rsi_sell_threshold)
                        sell_yn = sell_yn1 and sell_yn2
                        
                    elif trading_logic == 'stochastic_trading':
                        df = indicator.cal_stochastic_df(df, 14, 3)
                        _, sell_yn = logic.stochastic_trading(df)
                        
                    elif trading_logic == 'macd_trading':
                        df = indicator.cal_macd_df(df)
                        _, sell_yn = logic.macd_trading(candle, df)                                                    
                #매도 사인이 2개 이상일 때 quantity 조건에 충족되지 않은 조건은 history에 추가되지 않는다는 문제 해결 필요
                # 매도
                if sell_yn:
                    if trading_history['total_quantity'] > 0:
                        sell_quantity = (
                        trading_history['total_quantity']  # 보유 수량만큼만 매도
                        if trading_history['total_quantity'] < math.floor(trade_amount / close_price)
                        else math.floor(trade_amount / close_price))  # 대상 금액으로 매도 수량 계산
                        
                        # 실현 손익 계산
                        realized_pnl = (close_price - trading_history['average_price']) * sell_quantity                    
                        
                        trading_history['history'].append({
                            'position': 'SELL',
                            'trading_logic': trading_logic,
                            'price': close_price,
                            'quantity': sell_quantity,
                            'time': timestamp_iso,
                            'realized_pnl' : realized_pnl 
                        })
                        sell_signals.append((timestamp, close_price))
                        print(f"매도 시점: {timestamp_iso}, 매도가: {close_price} KRW, 매도량: {sell_quantity}")
                
                    
                    # 손익 및 매매 횟수 계산
                    trading_history = self.calculate_pnl(trading_history, close_price, trading_history['initial_capital'])

            print(f"총 비용: {trading_history['total_cost']}KRW, 총 보유량: {trading_history['total_quantity']}주, 평균 단가: {trading_history['average_price']}KRW, "
                f"실현 손익 (Realized PnL): {trading_history['realized_pnl']}KRW, 미실현 손익 (Unrealized PnL): {trading_history['unrealized_pnl']}KRW")
            
            # D-2, D-1 업데이트
            d_3 = d_2
            d_2 = d_1
            d_1 = candle
            i += 1

        # 캔들 차트 데이터프레임 생성
        result_data = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)
        print(f"result_data : {result_data}")
        # 매매 내역 요약 출력
        print("\n=== 매매 요약 ===")
        print(f"총 매수 횟수: {trading_history['buy_count']}")
        print(f"총 매도 횟수: {trading_history['sell_count']}")
        print(f"매수 날짜: {trading_history['buy_dates']}")
        print(f"매도 날짜: {trading_history['sell_dates']}")
        print(f"총 실현손익: {trading_history['realized_pnl']}KRW")
        print(f"미실현 손익 (Unrealized PnL): {trading_history['unrealized_pnl']}KRW")
        
        return result_data, trading_history, trade_reasons


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
    def trade(self, trading_bot_name, buy_trading_logic, sell_trading_logic, symbol, symbol_name, start_date, end_date, target_trade_value_krw, interval='day'):
        
        ohlc_data = self._get_ohlc(symbol, start_date, end_date, interval)
        trade_amount = target_trade_value_krw  # 매매 금액 (krw)

        closes = [float(candle.close) for candle in ohlc_data[:-1]]
        previous_closes = [float(candle.close) for candle in ohlc_data[:-2]]  # 마지막 봉을 제외한 종가들

        # 마지막 봉 데이터 (마지막 봉이란 당일)
        candle = ohlc_data[-1]
        open_price = float(candle.open)
        high_price = float(candle.high)
        low_price = float(candle.low)
        close_price = float(candle.close)
        volume = float(candle.volume)
        timestamp = candle.time

        # 마지막 직전 봉 데이터
        previous_candle = ohlc_data[-2]
        prev_open_price = float(previous_candle.open)
        prev_close_price = float(previous_candle.close)

        # 이전 캔들
        d_1 = ohlc_data[-2]  # 직전 봉
        d_2 = ohlc_data[-3]  # 전전 봉

        recent_20_days_volume = []
        avg_volume_20_days = 0

        if len(ohlc_data) >= 21:
            recent_20_days_volume = [float(c.volume) for c in ohlc_data[-20:]]
            avg_volume_20_days = sum(recent_20_days_volume) / len(recent_20_days_volume)
        
        # 볼린저 밴드 계산
        bollinger_band = indicator.cal_bollinger_band(previous_closes, close_price)
        
        # rsi
        rsi_buy_threshold = 35
        rsi_sell_threshold = 70

        for trading_logic in buy_trading_logic:
            buy_yn = False # 각 로직에 대한 매수 신호 초기화

            if trading_logic == 'check_wick':            
                buy_yn, _ = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
            elif trading_logic == 'rsi_trading':
                rsi_values = indicator.cal_rsi(closes, 14)
                buy_yn, _ = logic.rsi_trading(rsi_values, rsi_buy_threshold, rsi_sell_threshold)
            
            print(f'{trading_logic} 로직 buy_signal = {buy_yn}')

            self._trade_kis(
                buy_yn=buy_yn,
                sell_yn=False,
                volume=volume,
                d_1=d_1,
                avg_volume_20_days=avg_volume_20_days,
                trading_logic=trading_logic,
                symbol=symbol,
                symbol_name=symbol_name,
                ohlc_data=ohlc_data,
                trading_bot_name=trading_bot_name
            )

        for trading_logic in sell_trading_logic:
            sell_yn = False
            
            if trading_logic == 'check_wick':            
                # 볼린저 밴드 계산
                _, sell_yn = logic.check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])
            elif trading_logic == 'rsi_trading':
                rsi_values = indicator.cal_rsi(closes, 14)
                _, sell_yn = logic.rsi_trading(rsi_values, rsi_buy_threshold, rsi_sell_threshold)
            
            print(f'{trading_logic} 로직 sell_signal = {sell_yn}')

            self._trade_kis(
                buy_yn=False,
                sell_yn=sell_yn,
                volume=volume,
                d_1=d_1,
                avg_volume_20_days=avg_volume_20_days,
                trading_logic=trading_logic,
                symbol=symbol,
                symbol_name=symbol_name,
                ohlc_data=ohlc_data,
                trading_bot_name=trading_bot_name
            )

        # 마지막 직전 봉 음봉, 양봉 계산
        is_bearish_prev_candle = prev_close_price < prev_open_price  # 음봉 확인
        is_bullish_prev_candle = prev_close_price > prev_open_price  # 양봉 확인

        print(f'마지막 직전 봉 : {prev_close_price - prev_open_price}. 양봉 : {is_bullish_prev_candle}, 음봉 : {is_bearish_prev_candle}')

        # if trading_logic == "penetrating":
        #     buy_yn = logic.penetrating(candle, d_1, d_2)            
        # elif trading_logic == "engulfing":
        #     buy_yn = logic.engulfing(candle, d_1, d_2)            
        # elif trading_logic == "engulfing2":
        #     buy_yn = logic.engulfing2(candle, d_1, d_2)            
        # elif trading_logic == "counterattack":
        #     buy_yn = logic.counterattack(candle, d_1, d_2)
        # elif trading_logic == "harami":
        #     buy_yn = logic.harami(candle, d_1, d_2)
        # elif trading_logic == "doji_star":
        #     buy_yn = logic.doji_star(candle, d_1, d_2)
        # elif trading_logic == "morning_star":
        #     buy_yn = logic.morning_star(candle, d_1, d_2)

        # 가격 조회
        # DB 에서 종목 조회
        # 체결 강도 로직 조회

        return None
    

    def _trade_kis(self, buy_yn, sell_yn, volume, d_1, avg_volume_20_days, trading_logic, symbol, symbol_name, ohlc_data, trading_bot_name):

        if buy_yn and volume > d_1.volume and d_1.volume > avg_volume_20_days:                                 
            # 매수 함수 구현
            # trade()

            self.send_discord_webhook(f"[{trading_logic}] {symbol_name} 매수가 완료되었습니다. 매수금액 : {int(ohlc_data[-1].close)}KRW", "trading")

            # trade history 에 추가
            position = 'BUY'
            quantity = 1 # 임시

            self._insert_trading_history(trading_logic, position, trading_bot_name, ohlc_data[-1].close, quantity, symbol, symbol_name)
        
        if sell_yn:
            # 매도 함수 구현
            self.send_discord_webhook(f"[{trading_logic}] {symbol_name} 매도가 완료되었습니다. 매도금액 : {int(ohlc_data[-1].close)}KRW", "trading")
            # trade history 에 추가
            position = 'SELL'
            quantity = 1 # 임시

            self._insert_trading_history(trading_logic, position, trading_bot_name, ohlc_data[-1].close, quantity, symbol, symbol_name)


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

        # sql_executor = SQLExecutor()
        
        # 동적 쿼리 생성
        # query = """
        #     INSERT INTO fsts.trading_history
        #     (trading_logic, "position", trading_bot_name, price, quantity, symbol, symbol_name, trade_date)
        #     VALUES (:trading_logic, :position, :trading_bot_name, :price, :quantity, :symbol, :symbol_name, :trade_date)
        #     RETURNING *;
        # """
        
        # params = {
        #     "trading_logic": trading_logic,
        #     "position": position,
        #     "trading_bot_name": trading_bot_name,
        #     "price": price,
        #     "quantity": quantity,
        #     "symbol": symbol,
        #     "symbol_name": symbol_name,
        #     "trade_date": current_time
        # }

        # with get_db_session() as db:
        #     result = sql_executor.execute_upsert(db, query, params)

        return result


    # 컷 로스 (손절)
    def cut_loss(self, target_trade_value_usdt):
        pass