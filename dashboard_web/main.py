import sys
import os
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from st_aggrid import AgGrid
import pandas as pd
from datetime import datetime, date, timedelta
import pytz

from streamlit_lightweight_charts import renderLightweightCharts
import json
import numpy as np

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.crud_sql import SQLExecutor
from app.utils.database import get_db, get_db_session
from app.utils.dynamodb.model.stock_symbol_model import StockSymbol
from app.utils.dynamodb.model.trading_history_model import TradingHistory


def draw_lightweight_chart(data_df):

    # 차트 color
    COLOR_BULL = 'rgba(38,166,154,0.9)' # #26a69a
    COLOR_BEAR = 'rgba(239,83,80,0.9)'  # #ef5350

    # Some data wrangling to match required format
    data_df = data_df.reset_index()
    data_df.columns = [col.lower() for col in data_df.columns]

    buy_signal_df = data_df[data_df['buy_signal'].notna()]
    sell_signal_df = data_df[data_df['sell_signal'].notna()]

    # export to JSON format
    candles = json.loads(data_df.to_json(orient = "records"))

    bollinger_band_upper = json.loads(data_df.dropna(subset=['upper']).rename(columns={"upper": "value",}).to_json(orient = "records"))
    bollinger_band_middle = json.loads(data_df.dropna(subset=['middle']).rename(columns={"middle": "value",}).to_json(orient = "records"))
    bollinger_band_lower = json.loads(data_df.dropna(subset=['lower']).rename(columns={"lower": "value",}).to_json(orient = "records"))
    rsi = json.loads(data_df.dropna(subset=['rsi']).rename(columns={"rsi": "value"}).to_json(orient="records"))
    macd = json.loads(data_df.dropna(subset=['macd']).rename(columns={"macd": "value"}).to_json(orient="records"))
    macd_signal = json.loads(data_df.dropna(subset=['macd_signal']).rename(columns={"macd_signal": "value"}).to_json(orient="records"))
    macd_histogram = json.loads(data_df.dropna(subset=['macd_histogram']).rename(columns={"macd_histogram": "value"}).to_json(orient="records"))
    stochastic_k = json.loads(data_df.dropna(subset=['stochastic_k']).rename(columns={"stochastic_k": "value"}).to_json(orient="records"))
    stochastic_d = json.loads(data_df.dropna(subset=['stochastic_d']).rename(columns={"stochastic_d": "value"}).to_json(orient="records"))

    temp_df = data_df
    temp_df['color'] = np.where(temp_df['open'] > temp_df['close'], COLOR_BEAR, COLOR_BULL)  # bull or bear
    volume = json.loads(temp_df.rename(columns={"volume": "value",}).to_json(orient = "records"))

    # 매매 마커 추가
    markers = []
    for _, row in buy_signal_df.iterrows():
        marker = {
            "time": row['time'],  # 'date' 열을 'time' 키로 변환
            "position": "belowBar",  # 'position_type' 열을 'position' 키로 변환
            "color": "rgba(0, 0, 0, 1)",  # 'marker_color' 열을 'color' 키로 변환
            "shape": "arrowUp",  # 'marker_shape' 열을 'shape' 키로 변환
            "text": "B",  # 'type' 열을 'text' 키로 변환
            "size": 1  # 'size' 열을 'size' 키로 변환
        }
        markers.append(marker)

    for _, row in sell_signal_df.iterrows():
        marker = {
            "time": row['time'],  # 'date' 열을 'time' 키로 변환
            "position": "aboveBar",  # 'position_type' 열을 'position' 키로 변환
            "color": "rgba(0, 0, 0, 1)",  # 'marker_color' 열을 'color' 키로 변환
            "shape": "arrowDown",  # 'marker_shape' 열을 'shape' 키로 변환
            "text": "S",  # 'type' 열을 'text' 키로 변환
            "size": 1  # 'size' 열을 'size' 키로 변환
        }
        markers.append(marker)

    markers.sort(key=lambda marker: marker['time'])

    chartMultipaneOptions = [
        {
            # "width": 200, # 자동 너비 설정
            "height": 400,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": 'white'
                },
                "textColor": "black"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                    },
                "horzLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                }
            },
            "crosshair": {
                "mode": 0
            },
            "priceScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)"
            },
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,             # 왼쪽 가장자리 고정 여부
                "fixRightEdge": True,
                "visible": True
            },
        },
        {
            # "width": 1000,
            "height": 150,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": 'white'
                },
                "textColor": "black"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                    },
                "horzLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                }
            },
            "crosshair": {
                "mode": 0
            },
            "priceScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)"
            },
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,             # 왼쪽 가장자리 고정 여부
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'Volume',
            }
        },
        {
            "height": 150,  # RSI 차트 높이 설정
            "layout": {
                "background": {"type": "solid", "color": 'white'},
                "textColor": "black"
            },
            "grid": {
                "vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}
            },
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'RSI',
            }
        },
        {
            "height": 150,  # RSI 차트 높이 설정
            "layout": {
                "background": {"type": "solid", "color": 'white'},
                "textColor": "black"
            },
            "grid": {
                "vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}
            },
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'MACD',
            }
        },
        {
            "height": 150,  # RSI 차트 높이 설정
            "layout": {
                "background": {"type": "solid", "color": 'white'},
                "textColor": "black"
            },
            "grid": {
                "vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}
            },
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'Stocastic',
            }
        }
    ]

    seriesCandlestickChart = [
        {
            "type": 'Line',
            "data": bollinger_band_upper,  # 중앙선 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        },
        {
            "type": 'Line',
            "data": bollinger_band_middle,  # 상단 밴드 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        },
        {
            "type": 'Line',
            "data": bollinger_band_lower,  # 하단 밴드 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        },
        {
            "type": 'Candlestick',
            "data": candles,
            "options": {
                "upColor": COLOR_BULL,
                "downColor": COLOR_BEAR,
                "borderVisible": False,
                "wickUpColor": COLOR_BULL,
                "wickDownColor": COLOR_BEAR
            },
            "markers": markers
        },
    ]

    seriesVolumeChart = [
        {
            "type": 'Histogram',
            "data": volume,
            "options": {
                "priceFormat": {
                    "type": 'volume',
                },
                "priceScaleId": "", # set as an overlay setting,
                "priceLineVisible": False,
            },
            "priceScale": {
                "scaleMargins": {
                    "top": 0.1,
                    "bottom": 0,
                },
                "alignLabels": False
            },
        }
    ]

    # RSI 차트 시리즈 추가
    seriesRsiChart = [
        {
            "type": 'Line',
            "data": rsi,
            "options": {
                "color": 'rgba(0, 0, 0, 1)',
                "lineWidth": 1.5,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
        },
        {
            "type": 'Line',
            "data": [{"time": row["time"], "value": 70} for row in rsi],  # 과매수 라인
            "options": {
                "color": 'rgba(200, 0, 0, 0.5)',  # 빨간색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
        },
        {
            "type": 'Line',
            "data": [{"time": row["time"], "value": 30} for row in rsi],  # 과매도 라인
            "options": {
                "color": 'rgba(200, 0, 0, 0.5)',  # 빨간색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
        },
    ]

    seriesMACDChart = [
        {
            "type": 'Line',
            "data": macd,
            "options": {
                "color": 'rgba(0, 150, 255, 1)',
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line',
            "data": macd_signal, 
            "options": {
                "color": 'rgba(255, 0, 0, 1)', 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Histogram',
            "data": macd_histogram,
            "options": {
                "priceLineVisible": False,
            }
        }
    ]

    seriesStochasticChart = [
        {
            "type": 'Line', 
            "data": stochastic_k, 
            "options": {
                "color": 'rgba(0, 150, 255, 1)', 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line', 
            "data": stochastic_d, 
            "options": {
                "color": 'rgba(255, 0, 0, 1)', 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
    ]

    renderLightweightCharts([
        {
            "chart": chartMultipaneOptions[0],
            "series": seriesCandlestickChart
        },
        {
            "chart": chartMultipaneOptions[1],
            "series": seriesVolumeChart
        },
        {
            "chart": chartMultipaneOptions[2],
            "series": seriesRsiChart
        },
        {
            "chart": chartMultipaneOptions[3],
            "series": seriesMACDChart
        },
        {
            "chart": chartMultipaneOptions[4],
            "series": seriesStochasticChart
        },
    ], 'multipane')

def rename_tradingLogic(trade_history):
    for entry in trade_history:
        if entry.get('trading_logic') == 'rsi_trading':  # history에 있는 로직 이름 변경
            entry['trading_logic'] = 'rsi 확인'
        elif entry.get('trading_logic') == 'check_wick':
            entry['trading_logic'] = '꼬리 확인'
        elif entry.get('trading_logic') == 'penetrating':
            entry['trading_logic'] = '관통형'
        elif entry.get('trading_logic') == 'morning_star':
            entry['trading_logic'] = '샛별형'
        elif entry.get('trading_logic') == 'doji_star':
            entry['trading_logic'] = '상승도지스타'
        elif entry.get('trading_logic') == 'harami':
            entry['trading_logic'] = '상승잉태형'
        elif entry.get('trading_logic') == 'engulfing':
            entry['trading_logic'] = '상승장악형'
        elif entry.get('trading_logic') == 'engulfing2':
            entry['trading_logic'] = '상승장악형2'
        elif entry.get('trading_logic') == 'counterattack':
            entry['trading_logic'] = '상승반격형'
        elif entry.get('trading_logic') == 'down_engulfing':
            entry['trading_logic'] = '하락장악형'
        elif entry.get('trading_logic') == 'down_engulfing2':
            entry['trading_logic'] = '하락장악형2'    
        elif entry.get('trading_logic') == 'down_counterattack':
            entry['trading_logic'] = '하락반격형'
        elif entry.get('trading_logic') == 'down_harami':
            entry['trading_logic'] = '하락잉태형'
        elif entry.get('trading_logic') == 'down_doji_star':
            entry['trading_logic'] = '하락도지스타'
        elif entry.get('trading_logic') == 'evening_star':
            entry['trading_logic'] = '석별형'
        elif entry.get('trading_logic') == 'dark_cloud':
            entry['trading_logic'] = '흑운형'
        elif entry.get('trading_logic') == 'mfi_trading':
            entry['trading_logic'] = 'mfi 확인'


def setup_sidebar(sql_executer):
    """
    공통적으로 사용할 사이드바 UI를 설정하는 함수
    """
    
    st.sidebar.header("Simulation Settings")

    user_name = '홍석형'

    # AutoTradingBot 및 SQLExecutor 객체 생성
    sql_executor = SQLExecutor()
    auto_trading_stock = AutoTradingBot(user_name=user_name, virtual=False)
    
    current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    # 사용자 입력
    # user_name = st.sidebar.text_input("User Name", value="홍석문")
    start_date = st.sidebar.date_input("Start Date", value=date(2023, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=current_date_kst)
    target_trade_value_krw = st.sidebar.number_input("Target Trade Value (KRW)", value=1000000, step=100000)

    result = list(StockSymbol.scan(
        filter_condition=(StockSymbol.type == 'kospi200')
    ))

    # Dropdown 메뉴를 통해 데이터 선택
    symbol_options = {
        # "삼성전자": "352820",
        # "대한항공": "003490",
    }

    for stock in result:
        key = stock.symbol_name  # 'a' 값을 키로
        value = stock.symbol  # 'b' 값을 값으로
        symbol_options[key] = value  # 딕셔너리에 추가
            
    # interval 설정
    interval_options = {
        "DAY": "day",
        "WEEK": "week",
        "MONTH": "month",
    }

    # 매수/매도 로직 설정
    # JSON 파일 읽기
    file_path = "./dashboard_web/trading_logic.json"
    with open(file_path, "r", encoding="utf-8") as file:
        trading_logic = json.load(file)

    # 사용 예시
    available_buy_logic = trading_logic["available_buy_logic"]
    available_sell_logic = trading_logic["available_sell_logic"]
    
    selected_stock = st.sidebar.selectbox("Select a Stock", list(symbol_options.keys()))
    selected_interval = st.sidebar.selectbox("Select Chart Interval", list(interval_options.keys()))
    selected_buy_logic = st.sidebar.multiselect("Select Buy Logic(s):", list(available_buy_logic.keys()))
    selected_sell_logic = st.sidebar.multiselect("Select Sell Logic(s):", list(available_sell_logic.keys()))
    
    # 3% 매수 조건 체크박스 (체크하면 'Y', 체크 해제하면 'N')
    buy_condition_enabled = st.sidebar.checkbox("매수 제약 조건 활성화")  # True / False 반환
    buy_condition_yn = "Y" if buy_condition_enabled else "N"
    
    # 사용자가 직접 매수 퍼센트 (%) 입력 (기본값 3%)
    if buy_condition_yn == 'Y':
        buy_percentage = st.sidebar.number_input("퍼센트 (%) 입력", min_value=0.0, max_value=100.0, value=3.0, step=0.1)
    else:
        buy_percentage = None
        
    symbol = symbol_options[selected_stock]
    interval = interval_options[selected_interval]
    
    selected_buyTrading_logic = [available_buy_logic[logic] for logic in selected_buy_logic] if selected_buy_logic else []
    selected_sellTrading_logic = [available_sell_logic[logic] for logic in selected_sell_logic] if selected_sell_logic else []

    # ✅ rsi 조건값 입력
    
    rsi_buy_threshold = st.sidebar.number_input("📉 RSI 매수 임계값", min_value=0, max_value=100, value=30, step=1)
    rsi_sell_threshold = st.sidebar.number_input("📈 RSI 매도 임계값", min_value=0, max_value=100, value=70, step=1)
    
    #mode
    ohlc_mode_checkbox = st.sidebar.checkbox("차트 연결 모드")  # True / False 반환
    ohlc_mode = "continuous" if ohlc_mode_checkbox else "default"
    
    # ✅ 설정 값을 딕셔너리 형태로 반환
    return {
        "user_name": user_name,
        "start_date": start_date,
        "end_date": end_date,
        "target_trade_value_krw": target_trade_value_krw,
        "kospi200": symbol_options,
        "symbol": symbol,
        "selected_stock": selected_stock,
        "interval": interval,
        "buy_trading_logic": selected_buyTrading_logic,
        "sell_trading_logic": selected_sellTrading_logic,
        "buy_condition_yn": buy_condition_yn,
        "buy_percentage": buy_percentage,
        "ohlc_mode": ohlc_mode,
        "rsi_buy_threshold" : rsi_buy_threshold,
        "rsi_sell_threshold" : rsi_sell_threshold
    }
    
def setup_my_page():
    """
    마이페이지 설정 탭: 사용자 맞춤 설정 저장
    """
    st.header("🛠 마이페이지 설정")

    # AutoTradingBot, trading_logic 및 SQLExecutor 객체 생성
    user_name = "홍석형"  # 사용자 이름 (고정값)
    auto_trading_stock = AutoTradingBot(user_name=user_name, virtual=False)
    
    current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()

    start_date = st.date_input("📅 Start Date", value=date(2023, 1, 1))
    end_date = st.date_input("📅 End Date", value=current_date_kst)
    target_trade_value_krw = st.number_input("💰 Target Trade Value (KRW)", value=1000000, step=100000)

    # ✅ DB에서 종목 리스트 가져오기
    kospi200_result = list(StockSymbol.scan(
        filter_condition=(StockSymbol.type == 'kospi200')
    ))

    symbol_options = {row.symbol_name: row.symbol for row in kospi200_result}
    stock_names = list(symbol_options.keys())
    
    # ✅ "전체 선택" 및 "선택 해제" 버튼 추가
    col1, col2 = st.columns([1, 6])
    
    with col1:
        if st.button("✅ 종목 전체 선택"):
            st.session_state["selected_stocks"] = stock_names

    with col2:
        if st.button("❌ 종목 선택 해제"):
            st.session_state["selected_stocks"] = []
            
    # ✅ 사용자가 원하는 종목 선택 (다중 선택 가능)
    selected_stocks = st.multiselect("📌 원하는 종목 선택", list(symbol_options.keys()), key="selected_stocks")
    selected_symbols = {stock: symbol_options[stock] for stock in selected_stocks}

    # ✅ 차트 간격 (interval) 설정
    interval_options = {"DAY": "day", "WEEK": "week", "MONTH": "month"}
    selected_interval = st.selectbox("⏳ 차트 간격 선택", list(interval_options.keys()), key="selected_interval")
    interval = interval_options[selected_interval]

    # ✅ 매수/매도 로직 설정
    file_path = "./dashboard_web/trading_logic.json"
    with open(file_path, "r", encoding="utf-8") as file:
        trading_logic = json.load(file)

    available_buy_logic = trading_logic["available_buy_logic"]
    available_sell_logic = trading_logic["available_sell_logic"]

    # ✅ 매수/매도 전략 선택
    selected_buy_logic = st.multiselect("📈 매수 로직 선택", list(available_buy_logic.keys()), key="selected_buy_logic")
    selected_sell_logic = st.multiselect("📉 매도 로직 선택", list(available_sell_logic.keys()), key="selected_sell_logic")

    selected_buyTrading_logic = [available_buy_logic[logic] for logic in selected_buy_logic] if selected_buy_logic else []
    selected_sellTrading_logic = [available_sell_logic[logic] for logic in selected_sell_logic] if selected_sell_logic else []

    # ✅ 3% 매수 조건 체크박스
    buy_condition_enabled = st.checkbox("💰 매수 제약 조건 활성화", key="buy_condition_enabled")
    buy_condition_yn = "Y" if buy_condition_enabled else "N"

    # ✅ 매수 퍼센트 입력
    buy_percentage = None
    if buy_condition_yn == "Y":
        buy_percentage = st.number_input("💵 퍼센트 (%) 입력", min_value=0.0, max_value=100.0, value=3.0, step=0.1, key="buy_percentage")

    # ✅ rsi 조건값 입력
    st.subheader("🎯 RSI 조건값 설정")
    rsi_buy_threshold = st.number_input("📉 RSI 매수 임계값", min_value=0, max_value=100, value=35, step=1, key="rsi_buy_threshold")
    rsi_sell_threshold = st.number_input("📈 RSI 매도 임계값", min_value=0, max_value=100, value=70, step=1, key="rsi_sell_threshold")

    # ✅ 설정 저장 버튼
    if st.button("✅ 설정 저장"):
        st.session_state["my_page_settings"] = {
            "user_name": user_name,
            "start_date": start_date,
            "end_date": end_date,
            "target_trade_value_krw": target_trade_value_krw,
            "selected_stocks": selected_stocks, #이름만
            "selected_symbols": selected_symbols, #이름+코드(key,value)
            "interval": interval,
            "selected_buyTrading_logic": selected_buyTrading_logic,
            "selected_sellTrading_logic": selected_sellTrading_logic,
            "buy_condition_yn": buy_condition_yn,
            "buy_percentage": buy_percentage,
            "rsi_buy_threshold": rsi_buy_threshold,
            "rsi_sell_threshold": rsi_sell_threshold
        }
        st.success("✅ 설정이 저장되었습니다!")

    # ✅ 저장된 설정 확인
    if "my_page_settings" in st.session_state:
        st.subheader("📌 저장된 설정값")
        st.write(st.session_state["my_page_settings"])

            
def main():
    
    # for DB
    sql_executor = SQLExecutor()

    st.set_page_config(layout="wide")
    
    # ✅ 공통 사이드바 설정 함수 실행 후 값 가져오기
    sidebar_settings = setup_sidebar(sql_executor)
    
    # 탭 생성
    tabs = st.tabs(["🏠 거래 내역", "📈 시뮬레이션 그래프", "📊 Data Analysis Page", "📊 KOSPI200 Simulation", "🛠 마이페이지 설정"])

    # 각 탭의 내용 구성
    with tabs[0]:
        st.header("🏠 트레이딩 봇 거래 내역")
        
        data = {
            "Trading Bot Name": [],
            "Trading Logic": [],
            "Trade Date": [],
            "Symbol Name": [],
            "Symbol": [],
            "Position": [],
            "Price": [],
            "Quantity": []
        }

        result = list(TradingHistory.scan())

        sorted_result = sorted(
            result,
            key=lambda x: (x.trading_logic, -x.trade_date, x.symbol_name) #trade_date 최신 순
        )
        
        for row in sorted_result:
            # 초 단위로 변환
            sec_timestamp = row.trade_date / 1000
            # 포맷 변환
            formatted_trade_date = datetime.fromtimestamp(sec_timestamp).strftime('%Y-%m-%d %H:%M:%S')

            data["Trading Bot Name"].append(row.trading_bot_name)
            data["Trading Logic"].append(row.trading_logic)
            data["Trade Date"].append(formatted_trade_date)
            data["Symbol Name"].append(row.symbol_name)
            data["Symbol"].append(row.symbol)
            data["Position"].append(row.position)
            data["Price"].append(f"{row.price:,.0f}")
            data["Quantity"].append(f"{row.quantity:,.0f}")

        df = pd.DataFrame(data)
        
        # AgGrid로 테이블 표시
        grid_response = AgGrid(
            df,
            editable=True,  # 셀 편집 가능
            sortable=True,  # 정렬 가능
            filter=True,    # 필터링 가능
            resizable=True, # 크기 조절 가능
            theme='streamlit',   # 테마 변경 가능 ('light', 'dark', 'blue', 등)
            fit_columns_on_grid_load=True  # 열 너비 자동 조정
        )

    with tabs[1]:
        st.header("📈 종목 시뮬레이션")
        
        if st.sidebar.button("개별 종목 시뮬레이션 실행", key = 'simulation_button'):
            auto_trading_stock = AutoTradingBot(user_name=sidebar_settings["user_name"], virtual=False)
            
            
            with st.container():
                st.write(f"📊 {sidebar_settings['selected_stock']} 시뮬레이션 실행 중...")
                
                #시뮬레이션 실행
                data_df, trading_history = auto_trading_stock.simulate_trading(
                    symbol=sidebar_settings["symbol"],
                    start_date=sidebar_settings["start_date"],
                    end_date=sidebar_settings["end_date"],
                    target_trade_value_krw=sidebar_settings["target_trade_value_krw"],
                    buy_trading_logic=sidebar_settings["buy_trading_logic"],
                    sell_trading_logic=sidebar_settings["sell_trading_logic"],
                    interval=sidebar_settings["interval"],
                    buy_percentage=sidebar_settings["buy_percentage"],
                    ohlc_mode = sidebar_settings["ohlc_mode"],
                    rsi_buy_threshold = sidebar_settings['rsi_buy_threshold'],
                    rsi_sell_threshold = sidebar_settings['rsi_sell_threshold']
                    
                )
        
                # tradingview chart draw
                draw_lightweight_chart(data_df)

                # # DB에서 trading_history 결과 조회
                # query = """
                #     SELECT *
                #     FROM fsts.simulation_history
                #     WHERE symbol = :symbol
                #     ORDER BY created_at DESC
                #     LIMIT 1
                # """
                # params = {"symbol": symbol}
                
                # with get_db_session() as db:
                #     trade_history = sql_executor.execute_select(db, query, params)
                
                if not trading_history:
                    st.write("No trading history available.")
                    return

                # 기본 거래 내역을 DataFrame으로 변환
                history_df = pd.DataFrame([trading_history])

                # 실현 수익률/미실현 수익률 컬럼이 존재하면 % 포맷 적용
                for column in ["realized_roi", "unrealized_roi"]:
                    if column in history_df.columns:
                        history_df[column] = history_df[column].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)
                        
                # 🎯 trading_history에 symbol 변수 추가
                stock_name = next((company for company, code in st.session_state.items() if code == sidebar_settings["symbol"]), "해당 종목 없음") #수정 필요!
                history_df["symbol"] = stock_name
                # 원하는 컬럼 순서 지정
                reorder_columns = [
                    "symbol", "average_price",
                    "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi", "total_cost",
                    "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity", "history", "created_at"
                ]
                
                # 재정렬된 컬럼만 선택
                history_df = history_df[[col for col in reorder_columns if col in history_df.columns]]

                # 데이터의 행과 열 전환 (Transpose) 후 테이블 표시
                history_df_transposed = history_df.transpose().reset_index()
                history_df_transposed.columns = ["Field", "Value"]

                # Streamlit에서 표시
                st.subheader("📊 Trading History Summary")
                st.dataframe(history_df_transposed, use_container_width=True)
                
                # 상세 거래 내역 처리
                if "history" in trading_history and isinstance(trading_history["history"], list) and trading_history["history"]:
                    # 트레이딩 로직명을 변환 (필요시)
                    rename_tradingLogic(trading_history["history"])  

                    # 상세 거래 내역을 DataFrame으로 변환
                    trade_history_df = pd.DataFrame(trading_history["history"])

                    # Streamlit에서 표시
                    st.subheader("📋 Detailed Trade History")
                    st.dataframe(trade_history_df, use_container_width=True)
                else:
                    st.write("No detailed trade history found.")


    with tabs[2]:
        st.header("📊 데이터 분석 페이지")
        
        # 데이터
        data = sns.load_dataset('penguins')

        # 히스토그램
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data, x='flipper_length_mm', hue='species', multiple='stack', ax=ax)
        ax.set_title("Seaborn 히스토그램")
        st.pyplot(fig)
        
        #새로 추가된 코스피 200 시뮬레이션 탭
    with tabs[3]:
        st.header("📊 선택한 종목 시뮬레이션 결과")

        # ✅ 시뮬레이션 실행 버튼
        if st.button("선택 종목 시뮬레이션 실행"):
            
            my_page_settings = st.session_state["my_page_settings"]
            
            st.write("🔄 선택한 종목에 대해 시뮬레이션을 실행합니다.")

            # ✅ 진행률 바 추가
            progress_bar = st.progress(0)
            progress_text = st.empty()  # 진행 상태 표시

            all_trading_results = []
            failed_stocks = []
            total_stocks = len(my_page_settings["selected_symbols"])
            
            for i, (stock_name, symbol) in enumerate(my_page_settings["selected_symbols"].items()):
                try:
                    with st.spinner(f"📊 {stock_name} ({i+1}/{total_stocks}) 시뮬레이션 실행 중..."):
                        auto_trading_stock = AutoTradingBot(user_name=my_page_settings["user_name"], virtual=False)

                        _, trading_history = auto_trading_stock.simulate_trading(
                            symbol=symbol,
                            start_date=my_page_settings["start_date"],
                            end_date=my_page_settings["end_date"],
                            target_trade_value_krw=my_page_settings["target_trade_value_krw"],
                            buy_trading_logic=my_page_settings["selected_buyTrading_logic"],
                            sell_trading_logic=my_page_settings["selected_sellTrading_logic"],
                            interval=my_page_settings["interval"],
                            buy_percentage=my_page_settings["buy_percentage"],
                            rsi_buy_threshold = my_page_settings['rsi_buy_threshold'],
                            rsi_sell_threshold = my_page_settings['rsi_sell_threshold']
                        )

                        if trading_history:
                            trading_history["symbol"] = stock_name
                            all_trading_results.append(trading_history)

                    # ✅ 진행률 업데이트
                    progress = (i + 1) / total_stocks
                    progress_bar.progress(progress)
                    progress_text.text(f"{int(progress * 100)}% 완료 ({i+1}/{total_stocks})")

                except Exception as e:
                    st.write(f"⚠️ {stock_name} 시뮬레이션 실패: {str(e)}")
                    failed_stocks.append(stock_name)

            st.success("✅ 코스피 200 시뮬레이션 완료!")
            
            # ✅ 시뮬레이션 결과를 `st.session_state`에 저장!(페이지 리셋해도 계속 저장하기 위함)
            st.session_state["kospi200_trading_results"] = all_trading_results

            # ✅ 시뮬레이션 결과를 `st.session_state`에서 가져와 사용
            if st.session_state["kospi200_trading_results"]:
                df_results = pd.DataFrame(st.session_state["kospi200_trading_results"])
                
                # 원하는 컬럼 순서 지정
                reorder_columns = [
                    "symbol", "average_price",
                    "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi", "total_cost",
                    "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity", "history", "created_at"
                ]
                
                # ✅ 데이터가 있는 컬럼만 유지
                df_results = df_results[[col for col in reorder_columns if col in df_results.columns]]

                # 수익률 컬럼이 존재하면 % 형식 변환
                for col in ["realized_roi", "unrealized_roi"]:
                    if col in df_results.columns:
                        df_results[col] = df_results[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)

                # ✅ 전체 합계 계산(총 실현 손익/미실현 손익)
                total_realized_pnl = df_results["realized_pnl"].sum()
                total_unrealized_pnl = df_results["unrealized_pnl"].sum()
                
                # ✅ 평균 실현 손익률 & 평균 미실현 손익률 (빈 값 제외)
                avg_realized_roi = df_results["realized_roi"].replace("%", "", regex=True).astype(float).mean()
                avg_unrealized_roi = df_results["unrealized_roi"].replace("%", "", regex=True).astype(float).mean()

                # ✅ 손익 요약 정보 표시
                st.subheader("📊 전체 종목 손익 요약")
                st.write(f"**💰 총 실현 손익:** {total_realized_pnl:,.2f} KRW")
                st.write(f"**📈 총 미실현 손익:** {total_unrealized_pnl:,.2f} KRW")
                st.write(f"**📊 평균 실현 손익률:** {avg_realized_roi:.2f}% KRW")
                st.write(f"**📉 평균 총 손익률:** {avg_unrealized_roi:.2f}% KRW")

                # ✅ 개별 종목별 결과 표시
                st.subheader("📋 종목별 시뮬레이션 결과")
                AgGrid(
                    df_results,
                    editable=True,
                    sortable=True,
                    filter=True,
                    resizable=True,
                    theme='streamlit',
                    fit_columns_on_grid_load=True
                )

                # ✅ 실패한 종목이 있다면 표시
                if failed_stocks:
                    st.warning(f"⚠️ 시뮬레이션 실패 종목 ({len(failed_stocks)}개): {', '.join(failed_stocks)}")

            else:
                st.write("⚠️ 시뮬레이션 결과가 없습니다.")
                
    with tabs[4]:  # 🛠 마이페이지 설정
        setup_my_page()            
    

if __name__ == "__main__":
    main()