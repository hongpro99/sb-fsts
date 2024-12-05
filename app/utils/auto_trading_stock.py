import datetime
import numpy as np
import pandas as pd
import requests
import math
from pykis import PyKis, KisChart, KisStock, KisAuth
from datetime import date, time
import mplfinance as mpf
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

class AutoTradingStock:
    def __init__(self, id, api_key, secret_key, account, virtual=True):
        self.virtual = virtual # 모의투자 여부 저장

        # KisAuth 객체 생성
        self.auth = KisAuth(
            id=id,
            appkey=api_key,
            secretkey=secret_key,
            account=account,
            virtual=virtual
            
        )
        # PyKis 객체 생성 및 초기화
        self.kis = PyKis(self.auth)
        
        print(f"{'모의투자' if self.virtual else '실전투자'} 계좌가 선택되었습니다.")
        

    def get_auth_info(self):
        """인증 정보 확인"""
        return {
            "id": self.auth.id,
            "account": self.auth.account,
            "virtual": self.virtual
            
            
        }

    def send_discord_webhook(self, message, bot_type):
        if bot_type == 'trading':
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL')  # 복사한 Discord 웹훅 URL로 변경
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

        
    # 실시간 매매 시뮬레이션 함수
    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw):
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)
        realized_pnl = 0
        trade_amount = target_trade_value_krw  # 매매 금액 (krw)
        position = 0  # 현재 포지션 수량
        total_buy_budget = 0  # 총 매수 가격
        trade_stack = []  # 매수 가격을 저장하는 스택
        previous_closes = []  # 이전 종가들을 저장

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
            bollinger_band = self._cal_bollinger_band(previous_closes, close_price)

            upper_wick, lower_wick = self._check_wick(candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper'])

            if lower_wick:  # 아랫꼬리일 경우 매수 (추가 매수 가능)
                position += 1
                trade_stack.append(open_price)
                buy_signals.append((timestamp, open_price))

                total_buy_budget += open_price * (trade_amount / open_price)  # 총 매수 금액 누적
                # 평균 매수 단가 계산
                average_entry_price = total_buy_budget / position

                # 매수 알림 전송
                message = (
                f"📈 매수 이벤트 발생!\n"
                f"종목: {symbol}\n"
                f"매수가: {open_price:.2f} KRW\n"
                f"매수 시점: {timestamp}\n"
                f"총 포지션: {position}\n"
                f"평균 매수 단가: {average_entry_price:.2f} KRW"
                )
                self.send_discord_webhook(message, "trading")
                print(f"매수 시점: {timestamp}, 진입가: {open_price:.7f} KRW, 총 포지션: {position}, 평균 매수 단가: {average_entry_price:.7f} KRW")

            elif upper_wick and position > 0:  # 윗꼬리일 경우 매도 (매수한 횟수의 1/n 만큼 매도)
                exit_price = next_open_price
                entry_price = trade_stack.pop()  # 스택에서 매수 가격을 가져옴
                pnl = (exit_price - entry_price) * math.floor(trade_amount / entry_price) # 주식 수 연산 및 곱하기
                realized_pnl += pnl
                sell_signals.append((next_timestamp, exit_price))
                position -= 1

                total_buy_budget -= entry_price * (trade_amount / entry_price)  # 매도 시 매수 금액에서 차감
                # 평균 매수 단가 계산
                average_entry_price = total_buy_budget / position if position > 0 else 0

                # 매도 알림 전송
                message = (
                f"📉 매도 이벤트 발생!\n"
                f"종목: {symbol}\n"
                f"매도가: {exit_price:.2f} KRW\n"
                f"매도 시점: {next_timestamp}\n"
                f"실현 손익: {pnl:.2f} KRW\n"
                f"남은 포지션: {position}\n"
                f"평균 매수 단가: {average_entry_price:.2f} KRW"
                )
                self.send_discord_webhook(message, "trading")
                
                print(f"매도 시점: {next_timestamp}, 최근 매수가(스택): {entry_price} KRW, 청산가: {exit_price} KRW, 매매 주식 수: {math.floor(trade_amount / entry_price)}, 실현 손익: {pnl:.7f} krw, 남은 포지션: {position}, 평균 매수 단가: {average_entry_price:.7f} KRW")

            i += 1

        # 마지막 봉의 close와 평균 매수 단가를 비교
        final_close = float(ohlc_data[-1].close)
        if position > 0:
            current_pnl = (final_close - (total_buy_budget / position)) * position * (trade_amount / final_close)
            print(f"현재 평균 매수 단가: {total_buy_budget / position:.7f} KRW")
            print(f"마지막 봉의 종가: {final_close:.7f} KRW")
            print(f"현재 가격 대비 평가 손익: {current_pnl:.7f} KRW")
        else:
            current_pnl = 0
            print(f"현재 포지션 없음. 마지막 봉의 종가: {final_close:.7f} KRW")

        # 캔들 차트 데이터프레임 생성
        simulation_plot = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)

        return simulation_plot, realized_pnl, current_pnl