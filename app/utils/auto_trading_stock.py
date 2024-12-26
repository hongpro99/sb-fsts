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
import asyncio
from typing import List, Dict
from sqlalchemy.orm import Session
from app.utils.crud_sql import SQLExecutor
from app.utils.database import get_db_session



# .env 파일 로드
load_dotenv()



class AutoTradingStock:
    def __init__(self, id, account, real_appkey, real_secretkey, virtual=False, virtual_id=None, virtual_appkey=None, virtual_secretkey=None):
        """
        AutoTradingStock 클래스 초기화
        실전투자와 모의투자를 선택적으로 설정 가능
        """
        # 속성 초기화
        self.virtual = virtual
        self.id = id
        self.account = account  # 계좌 번호 저장
        self.appkey = real_appkey
        self.secretkey = real_secretkey
        self.virtual_id = virtual_id
        self.virtual_appkey = virtual_appkey
        self.virtual_secretkey = virtual_secretkey
        self.ticket = None  # 실시간 체결 구독 티켓
        self.kis = None  # kis 초기화
        self.sql_executor = SQLExecutor()
        
        if self.virtual:
            # 모의투자용 PyKis 객체 생성
            if not all([id,account, real_appkey, real_secretkey,virtual_id, virtual_appkey, virtual_secretkey]):
                raise ValueError("모의투자 정보를 완전히 제공해야 합니다.")
            
            message = ("모의투자 API 객체를 생성 중입니다...")
            self.send_discord_webhook(message,"trading")
            self.kis = PyKis(
                id=id,
                account=account,
                appkey=real_appkey,
                secretkey=real_secretkey,
                virtual_id=virtual_id,
                virtual_appkey=virtual_appkey,
                virtual_secretkey=virtual_secretkey,
                keep_token=True  # API 접속 토큰 자동 저장
            )
            
        else:
            # 실전투자용 PyKis 객체 생성
            message = ("실전투자 API 객체를 생성 중입니다...")
            self.send_discord_webhook(message,"trading")
            self.kis = PyKis(
                id=id,
                account=account,
                appkey=real_appkey,
                secretkey=real_secretkey,
                keep_token=True  # API 접속 토큰 자동 저장
            )
            

        print(f"{'모의투자' if self.virtual else '실전투자'} API 객체가 성공적으로 생성되었습니다.")

        
    def get_account_info(self):
        """투자 유형 및 계좌 정보를 반환"""
        account_type = "모의 투자" if self.virtual else "실전 투자"
        return {
            "투자 유형": account_type,
            "계좌 번호": self.account,
            "사용된 ID": self.virtual_id if self.virtual else self.id

        }

    def send_account_info_to_discord(self):
        """계좌 정보를 디스코드 웹훅에 전송"""
        account_info = self.get_account_info()

        # 정보를 문자열로 정리
        message = (
            "📢 투자 계좌 정보:\n" +
            "\n".join([f"{key}: {value}" for key, value in account_info.items()])
        )

        # 디스코드로 전송
        self.send_discord_webhook(message, "trading")

    def get_access_token(self):
        """
        한국투자증권 API에서 액세스 토큰을 발급받는 함수
        """
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {
        "grant_type": "client_credentials",
        "appkey": os.getenv('API_KEY'),  # 본인의 appkey로 변경
        "appsecret": os.getenv('API_SECRET')  # 본인의 appsecret로 변경
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                token_data = response.json()
                print("토큰 발급 성공:", token_data)
                return token_data["access_token"]
            else:
                print(f"토큰 발급 실패: {response.status_code} {response.text}")
                return None
        except Exception as e:
            print(f"토큰 발급 중 오류 발생: {e}")
            return None    
        

    #def get_auth_info(self):
    #    """인증 정보 확인"""
    #    return {
    #        "id": self.id,
    #        "account": self.account,
    #        "virtual": self.virtual
            
            
    #    }

    def send_discord_webhook(self, message, bot_type):
        if bot_type == 'trading':
            webhook_url = os.getenv('TEST_DISCORD_WEBHOOK_URL')  # 복사한 Discord 웹훅 URL로 변경
            username = "FSTS trading Bot"
            
        elif bot_type == "simulation":
            webhook_url = os.getenv('TEST_DISCORD_SIMULATION_WEBHOOK_URL')  # 복사한 Discord 웹훅 URL로 변경
            username = "FSTS simulation Bot"

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


    def get_stock_quote(self, symbol):
        """주식 시세를 가져와 디스코드로 전달"""
        try:
            # 종목 객체 가져오기
            stock = self.kis.stock(symbol)

            # 시세 가져오기
            quote: KisQuote = stock.quote()
            quote: KisQuote = stock.quote(extended=True) # 주간거래 시세
        # 시세 정보 문자열 생성
            message = (
    f"📊 종목 시세 정보\n"
    f"종목 코드: {quote.symbol}\n"
    f"종목명: {quote.name}\n"
    f"업종: {quote.sector_name}\n"
    f"현재가: {quote.close:,.0f} KRW\n"
    f"시가: {quote.open:,.0f} KRW\n"
    f"고가: {quote.high:,.0f} KRW\n"
    f"저가: {quote.low:,.0f} KRW\n"
    f"전일 대비 가격: {quote.change:,.0f} KRW\n"
    f"등락률: {quote.change / (quote.close - quote.change):.2%}\n"
    f"거래량: {quote.volume:,.0f} 주\n"
    f"거래 대금: {quote.amount:,} KRW\n"
    f"시가총액: {quote.market_cap:,} 억 KRW\n"
    f"52주 최고가: {quote.indicator.week52_high:,.0f} KRW (일자: {quote.indicator.week52_high_date})\n"
    f"52주 최저가: {quote.indicator.week52_low:,.0f} KRW (일자: {quote.indicator.week52_low_date})\n"
    f"EPS (주당순이익): {quote.indicator.eps:,.0f} KRW\n"
    f"BPS (주당순자산): {quote.indicator.bps:,.0f} KRW\n"
    f"PER (주가수익비율): {quote.indicator.per}\n"
    f"PBR (주가순자산비율): {quote.indicator.pbr}\n"
    f"단위: {quote.unit}\n"
    f"호가 단위: {quote.tick:,.0f} KRW\n"
    f"거래 정지 여부: {'정지' if quote.halt else '정상'}\n"
    f"과매수 상태: {'예' if quote.overbought else '아니오'}\n"
    f"위험도: {quote.risk.capitalize()}\n"
    )
            # 디스코드 웹훅 전송
            self.send_discord_webhook(message,"simulation")

            # 디버깅용 출력
            print("주식 시세 정보:", message)
        except Exception as e:
            print(f"주식 시세 조회 중 오류 발생: {e}")
            error_message = f"❌ 주식 시세 조회 중 오류 발생: {e}"
            self.send_discord_webhook(error_message,"simulation")
            
    def inquire_balance(self):
        """잔고 정보를 디스코드 웹훅으로 전송"""
        
                # 주 계좌 객체를 가져옵니다.
        account = self.kis.account()

        balance: KisBalance = account.balance()

        print(repr(balance)) # repr을 통해 객체의 주요 내용을 확인할 수 있습니다.
        
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
            self.send_discord_webhook(message, "trading")

        except Exception as e:
            # 오류 메시지 처리
            error_message = f"❌ 잔고 정보를 처리하는 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")
    
    def place_order(self, symbol, qty, buy_price=None, sell_price=None, order_type="buy"):
        """주식 매수/매도 주문 함수
        Args:
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
                message = f"📈 매수 주문 완료! 종목: {symbol}, 수량: {qty}, 가격: {'시장가' if not buy_price else buy_price}"
            elif order_type == "sell":
                if sell_price:
                    order = stock.sell(price=sell_price)  # 지정가 매도
                else:
                    order = stock.sell()  # 시장가 매도
                message = f"📉 매도 주문 완료! 종목: {symbol}, 수량: {qty}, 가격: {'시장가' if not sell_price else sell_price}"
            else:
                raise ValueError("Invalid order_type. Must be 'buy' or 'sell'.")

            # 디스코드로 주문 결과 전송
            self.send_discord_webhook(message, "trading")

            return order

        except Exception as e:
            error_message = f"주문 처리 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")

    
    def get_trading_hours(self, country_code):
        """
        특정 국가의 주식 시장 거래 시간을 조회합니다.
        Args:
            country_code (str): 국가 코드 (예: US, KR, JP)
        """
        try:
            # 거래 시간 조회
            trading_hours: KisTradingHours = self.kis.trading_hours(country_code)

            # 메시지 정리
            message = (
                f"📅 **{country_code} 주식 시장 거래 시간**\n"
                f"정규 거래 시작: {trading_hours.open_kst}\n"
                f"정규 거래 종료: {trading_hours.close_kst}\n"
            )

            # 결과 출력 및 웹훅 전송
            print(message)
            self.send_discord_webhook(message, "trading")
            return message
        
        except Exception as e:
            error_message = f"❌ 거래 시간 조회 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")
            return None

    def get_investor_trend(self, market_code="KSP", industry_code="0001"):
        """
        시장별 투자자 매매동향을 조회합니다.
        Args:
            market_code (str): 시장 코드 (KSP: KOSPI, KSQ: KOSDAQ)
            industry_code (str): 업종 코드
        Returns:
            dict: 조회 결과
        """
        
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            'Authorization': str(self.kis.token),
            "appkey": self.appkey,
            "appsecret": self.secretkey,
            "tr_id": "FHPTJ04030000",
            "custtype" :"P" # 실전 거래용 TR_ID
        }
        
        params = {
            "fid_input_iscd": market_code,  # 시장 코드
            "fid_input_iscd_2": industry_code,  # 업종 코드
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                output = result.get("output", [])

                # 결과 메시지 생성
                if not output:  # output이 비어있을 경우 처리
                    self.send_discord_webhook("❌ 조회된 투자자 매매동향 데이터가 없습니다.", "trading")
                else:
                    # output은 단일 리스트로 가정
                    item = output[0]  # 리스트 내 첫 번째 항목 처리
                    message = (
                        f"**📊 {market_code} 투자자 매매동향 결과**\n"
                        f"외국인 매도 거래 대금: {item['frgn_seln_tr_pbmn']}\n"
                        f"외국인 매수 거래 대금: {item['frgn_shnu_tr_pbmn']}\n"
                        f"외국인 순매수 거래 대금: {item['frgn_ntby_tr_pbmn']}\n\n"
                        f"기관 매도 거래 대금: {item['orgn_seln_tr_pbmn']}\n"
                        f"기관 매수 거래 대금: {item['orgn_shnu_tr_pbmn']}\n"
                        f"기관 순매수 거래 대금: {item['orgn_ntby_tr_pbmn']}\n\n"
                        f"개인 매도 거래 대금: {item['prsn_seln_tr_pbmn']}\n"
                        f"개인 매수 거래 대금: {item['prsn_shnu_tr_pbmn']}\n"
                        f"개인 순매수 거래 대금: {item['prsn_ntby_tr_pbmn']}\n"
                    )
                    self.send_discord_webhook(message, "trading")
            else:
                error_message = f"❌ API 호출 실패: {response.status_code}, {response.text}"
                self.send_discord_webhook(error_message, "trading")
        except Exception as e:
            error_message = f"❌ 투자자매매동향 조회 중 오류 발생: {e}"
            self.send_discord_webhook(error_message,"trading")


# #직접 API 호출한 체결강도 순위 조회
#     def get_volume_power_ranking(self, market_code="J", input_market="2001"):
#         """
#         시장별 거래량 순위 조회 메소드
#         Args:
#         market_code (str): 시장 코드 (KOSPI: "J", KOSDAQ: "Q", 전체: "U")
#         """
#         # API 요청 URL
#         url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/volume-power"

#         # 요청 헤더 설정
#         headers = {
#             "Content-Type": "application/json; charset=utf-8",
#             "Authorization": str(self.kis.token),
#             "appkey": self.appkey,
#             "appsecret": self.secretkey,
#             "tr_id": "FHPST01680000",
#             "custtype": "P"
#         }

#         # 요청 파라미터 설정
#         params = {
#             "fid_trgt_exls_cls_code": "0",
#             "fid_cond_mrkt_div_code": market_code,
#             "fid_cond_scr_div_code": "20168",
#             "fid_input_iscd": input_market,
#             "fid_div_cls_code": "0",
#             "fid_input_price_1": "",
#             "fid_input_price_2": "",
#             "fid_vol_cnt": "",
#             "fid_trgt_cls_code": "0"
#         }

#         try:
#             # API 요청
#             response = requests.get(url, headers=headers, params=params)

#             if response.status_code == 200:
#                 result = response.json()
#                 rankings = result.get("output", [])
                
#                 # 조회된 결과를 문자열로 정리
#                 message = "**📊 체결강도 순위 조회 결과:**\n"
#                 for idx, stock in enumerate(rankings[:10]):  # 상위 10개 종목만 표시
#                     message += (
#                         f"{idx+1}. 종목명: {stock['hts_kor_isnm']}\n"
#                         f"종목코드: {stock["stck_shrn_iscd"]}\n"
#                         f"당일 체결강도: {stock['tday_rltv']}\n"
                        
#                     )
#                 print(message)
#                 self.send_discord_webhook(message, "trading")

#             else:
#                 error_message = f"❌ 거래량 순위 조회 실패: {response.status_code} {response.text}"
#                 print(error_message)
#                 self.send_discord_webhook(error_message, "trading")

#         except Exception as e:
#             error_message = f"❌ 거래량 순위 조회 중 오류 발생: {e}"
#             print(error_message)
#             self.send_discord_webhook(error_message, "trading")

#매도 과정은 빼기?
    def get_volume_power_ranking_and_trade(self, input_market="2001"):
        """
        체결강도 순위를 조회하고 조건에 따라 종목을 자동으로 매수/매도
        Args:
            market_code (str): 시장 코드 (KOSPI: "J", KOSDAQ: "Q", 전체: "U")
            input_market (str): 조회할 시장 코드
        """
        # API 요청 URL
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/volume-power"

        # 요청 헤더 설정
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": str(self.kis.token),
            "appkey": self.appkey,
            "appsecret": self.secretkey,
            "tr_id": "FHPST01680000",
            "custtype": "P"
        }

        # 요청 파라미터 설정
        params = {
            "fid_trgt_exls_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20168",
            "fid_input_iscd": input_market,
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_trgt_cls_code": "0"
        }

        try:
            # API 요청 보내기
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                rankings = result.get("output", [])

                # 메시지 구성
                message = "**📊 체결강도 상위 종목 조회 및 자동 매수/매도**\n"
                top_stocks = []

                for idx, stock in enumerate(rankings[:5]):  # 상위 5개 종목만 처리
                    stock_name = stock['hts_kor_isnm']
                    stock_code = stock['stck_shrn_iscd']
                    volume_power = float(stock['tday_rltv'])

                    message += (
                        f"{idx+1}. 종목명: {stock_name}\n"
                        f"종목코드: {stock_code}\n"
                        f"체결강도: {volume_power:.2f}\n"
                    )

                # 결과를 디스코드에 전송
                print(message)
                self.send_discord_webhook(message, "trading")


                # 체결강도 1위 종목 선택
                top_stock = rankings[0]
                stock_name = top_stock['hts_kor_isnm']
                stock_code = top_stock['stck_shrn_iscd']
                volume_power = float(top_stock['tday_rltv'])
                


                # 1주 매수 실행 (시장가)
                buy_qty = 1
                buy_price = None  # 시장가
                order_result = self.place_order(stock_code, buy_qty, buy_price, order_type="buy")

                if order_result:
                    self.send_discord_webhook(
                        f"✅ 매수 완료: 종목명: {stock_name}, 수량: {buy_qty}주, 가격: 시장가\n", "trading" 
                    )
                    
                    print(f"✅ 매수 완료: {stock_name} - 수량: {buy_qty}주")

                    # 매수 가격 저장
                    stock = self.kis.stock(stock_code)
                    quote = stock.quote()
                    purchase_price = float(quote.close)  # 매수가격 설정

                    # 5% 상승 시 매도 조건 확인
                    sell_price = round(purchase_price*1.05, 2)  # 매수가 대비 5% 상승
                    self.monitor_and_sell(stock_code, stock_name, buy_qty, purchase_price, sell_price)
                else:
                    self.send_discord_webhook(f"❌ 매수 실패: 종목명: {stock_name}", "trading")
            else:
                error_message = f"❌ 체결강도 조회 실패: {response.status_code}, {response.text}"
                print(error_message)
                self.send_discord_webhook(error_message, "trading")

        except Exception as e:
            error_message = f"❌ 체결강도 조회 및 자동매수 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")


    async def monitor_and_sell(self, stock_code, stock_name, qty, purchase_price, sell_price, timeout=1800, interval = 60):
        """
        매수가 대비 5% 상승 시 자동 매도
        """
        try:
            stock = self.kis.stock(stock_code)
            start_time = time.time()

            while True:
                # 현재 시간과 시작 시간 비교
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    self.send_discord_webhook(
                        f"⏳ 매도 조건 시간이 초과되었습니다. 목표가: {sell_price}원", "trading"
                    )
                    print("⏳ 매도 조건 시간이 초과되었습니다.")
                    break

                # 현재가 조회
                quote = stock.quote()
                current_price = float(quote.close)

                print(f"[{elapsed_time:.0f}초 경과] 현재가: {current_price}, 목표 매도가: {sell_price}")

                # 목표가 도달 시 매도 실행
                if current_price >= sell_price:
                    order_result = self.place_order(stock_code, qty, sell_price, order_type="sell")

                    if order_result:
                        profit = current_price - purchase_price
                        profit_rate = (profit / purchase_price) * 100

                        message = (
                            f"✅ 자동 매도 완료!\n"
                            f"종목명: {stock_name}\n"
                            f"매수가: {purchase_price}원\n"
                            f"매도가: {current_price}원\n"
                            f"수익률: {profit_rate:.2f}%"
                        )
                        print(message)
                        self.send_discord_webhook(message, "trading")
                    else:
                        self.send_discord_webhook(
                            f"❌ 매도 실패: 종목명: {stock_name}", "trading"
                        )
                    break

                # 일정 시간 대기
                await asyncio.sleep(interval)

        except Exception as e:
            error_message = f"❌ 매도 조건 확인 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")

    # 배당률 상위 조회 함수
    def get_top_dividend_stocks(self,db: Session):
        # 실전 투자 환경 URL
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/dividend-rate"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            'Authorization': str(self.kis.token),
            "appkey": self.appkey,
            "appsecret": self.secretkey,
            "tr_id": "HHKDB13470100",  # 실전 거래용 TR_ID
            "custtype": "P"
        }

        # 요청 쿼리 파라미터 설정
        params = {
            "CTS_AREA": "",
            "GB1": "0",  # 전체 조회 #0:전체, 1:코스피, 2: 코스피200, 3: 코스닥
            "UPJONG": "0001",  # 업종 코드 (예시) 코스피(0001:종합) 코스닥(1001:종합)
            "GB2": "6",  # 배당률 순서
            'GB3': '2',
            "F_DT": "20230101",  # 시작 날짜
            "T_DT": "20241201",  # 종료 날짜
            "GB4": "0"  # 기타 설정
        }

        # API 요청 보내기
        response = requests.get(url, headers=headers, params=params)

        # 응답 처리
        if response.status_code == 200:
            result = response.json()
            # 상위 5개 항목 추출
            top_stocks = result.get("output", [])[:5]

            # 결과 정리
            message = "📊 KOSPI 배당률 상위 5:\n"
            for idx, stock in enumerate(top_stocks):
                dividend_rate = float(stock['divi_rate']) / 100
                
                message +=(
                    f"{idx+1}. 종목명: {stock['isin_name']}\n"
                    f"날짜: {stock['record_date']}\n"
                    f"현금/주식배당금: {stock["per_sto_divi_amt"]}\n"
                    f"배당률: {dividend_rate:.2f}% \n"
                )
            
        
            # 디스코드 웹훅 전송
            self.send_discord_webhook(message, "trading")
                    
            # DB에 데이터 삽입
            for stock in top_stocks:
                query = """
                    INSERT INTO fsts.dividend_stocks (isin_name, record_date, per_sto_divi_amt, dividend_rate)
                    VALUES (:isin_name, :record_date, :per_sto_divi_amt, :dividend_rate)
                    RETURNING *
                """
                params = {
                    "isin_name": stock['isin_name'],
                    "record_date": stock['record_date'],
                    "per_sto_divi_amt": float(stock['per_sto_divi_amt']),
                    "dividend_rate": float(stock['divi_rate']) / 100
                }
                self.sql_executor.execute_insert(db, query, params)

            print("📊 배당률 상위 5종목이 DB에 저장되었습니다.")
            
        else:
            error_message = f"❌ 배당률 조회 실패: {response.status_code}, {response.text}"
            self.send_discord_webhook(error_message, "trading")
            print(error_message)


    def get_income_statement(self, symbol: str):
        """
        국내주식 손익계산서를 가져와 디스코드로 전송하는 함수
        Args:
            symbol (str): 종목 코드
        """
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/finance/income-statement"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": str(self.kis.token),
            "appkey": self.appkey,
            "appsecret": self.secretkey,
            "tr_id": "FHKST66430200",  # 실전 투자용 TR_ID
            "custtype": "P"
        }
        params = {
            "FID_DIV_CLS_CODE": "0",  # 0: 연도별 데이터, 1: 분기별 데이터
            "fid_cond_mrkt_div_code": "J",  # 시장 코드
            "fid_input_iscd": symbol  # 종목 코드
        }

        try:
            # API 호출
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            # API 실패 처리
            if result.get("rt_cd") != "0":
                error_message = f"⚠️ API 오류: {result.get('msg1')}"
                self.send_discord_webhook(error_message, "trading")
                return

            # 데이터 가져오기
            income_data = result.get("output", [])
            if not income_data:
                self.send_discord_webhook(f"⚠️ {symbol}에 대한 손익계산서 데이터가 없습니다.", "trading")
                return

            # 최근 2년 데이터 필터링
            current_year = datetime.now().year
            recent_data = [
                data for data in income_data if int(data["stac_yymm"][:4]) >= current_year - 2
            ]

            if not recent_data:
                self.send_discord_webhook(f"⚠️ 최근 2년간 손익계산서 데이터가 없습니다.", "trading")
                return

            # 메시지 생성
            message = f"📊 {symbol} 최근 3년간 손익계산서:\n"
            for data in recent_data:
                message += (
                    f"결산 년월: {data['stac_yymm']}\n"
                    f"매출액: {data['sale_account']} KRW\n"
                    f"매출 원가: {data['sale_cost']} KRW\n"
                    f"매출 총이익: {data['sale_totl_prfi']} KRW\n"
                    f"영업 이익: {data['bsop_prti']} KRW\n"
                    f"당기순이익: {data['thtr_ntin']} KRW\n"
                    f"-----------------------------\n"
                )

            # 디스코드에 메시지 전송
            self.send_discord_webhook(message, "trading")

        except requests.exceptions.RequestException as req_err:
            error_message = f"❌ API 호출 중 오류 발생: {req_err}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")

        except Exception as e:
            # 일반적인 예외 처리
            error_message = f"❌ 손익계산서 조회 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")
            
    def fetch_foreign_investor_data(self, symbol: str, start_date: str, end_date: str) -> list:
        """
        외국인 순매수 데이터를 가져옵니다.
        Args:
            symbol (str): 종목 코드
            start_date (str): 시작 날짜 (YYYY-MM-DD 형식)
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식)
        Returns:
            list: 특정 기간에 해당하는 외국인 순매수 데이터 리스트
        """
        try:
            print(f"[INFO] 외국인 순매수 데이터 가져오기 시작... 종목: {symbol}, 기간: {start_date} ~ {end_date}")

            # API 요청 URL
            url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-investor"

            # API 요청 헤더
            headers = {
                "authorization": str(self.kis.token),
                "appkey": self.appkey,
                "appsecret": self.secretkey,
                "tr_id": "FHKST01010900",  # 실전 거래용 TR_ID
            }

            # API 요청 파라미터
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 코드 (KOSPI)
                "FID_INPUT_ISCD": symbol,  # 종목 코드
            }

            # API 요청
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            # 응답 데이터 파싱
            result = response.json()

            if result.get("rt_cd") != "0":
                print(f"[WARNING] API 호출 실패: {result.get('msg1')}")
                self.send_discord_webhook(f"⚠️ API 호출 실패: {result.get('msg1')}", "simulation")
                return []

            all_data = result.get("output", [])
            if not all_data:
                print(f"[INFO] {symbol}에 대한 데이터가 없습니다.")
                return []

            # 데이터 필터링: 사용자 지정 날짜에 맞는 데이터만 반환
            filtered_data = []
            for entry in all_data:
                entry_date = entry["stck_bsop_date"]
                print(f"[DEBUG] 반환된 데이터 날짜: {entry_date}")  # 반환된 날짜 확인

                if start_date <= entry_date <= end_date:
                    filtered_data.append({
                        "symbol": symbol,
                        "date": entry_date,  # 날짜
                        "foreign_net_buy": float(entry["frgn_ntby_tr_pbmn"]),  # 외국인 순매수 거래 대금
                        "close_price": float(entry["stck_clpr"]),  # 종가
                    })

            print(f"[INFO] 데이터 변환 완료! 총 {len(filtered_data)}개의 데이터가 준비되었습니다.")
            return filtered_data

        except Exception as e:
            print(f"[ERROR] 외국인 순매수 데이터 가져오는 중 오류 발생: {e}")
            self.send_discord_webhook(f"❌ 외국인 순매수 데이터 가져오는 중 오류 발생: {e}", "simulation")
            return []


            
            



