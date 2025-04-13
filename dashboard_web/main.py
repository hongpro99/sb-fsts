import sys
import os
import io
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder
import pandas as pd
from datetime import datetime, date, timedelta
import pytz
import streamlit.components.v1 as components
from streamlit_lightweight_charts import renderLightweightCharts
import json
import numpy as np

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.crud_sql import SQLExecutor
from app.utils.database import get_db, get_db_session
from app.utils.trading_logic import TradingLogic
from app.utils.dynamodb.model.stock_symbol_model import StockSymbol
from app.utils.dynamodb.model.trading_history_model import TradingHistory
from app.utils.dynamodb.model.user_info_model import UserInfo
from app.utils.dynamodb.model.auto_trading_balance_model import AutoTradingBalance
from app.utils.technical_indicator import TechnicalIndicator


#보조지표 클래스 선언
logic = TradingLogic()

def draw_lightweight_chart(data_df, selected_indicators):

    # 차트 color
    COLOR_BULL = 'rgba(236, 57, 72, 1)' # #26a69a
    COLOR_BEAR = 'rgba(74, 86, 160, 1)'  # #ef5350

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

    ema_60 = json.loads(data_df.dropna(subset=['ema_60']).rename(columns={"ema_60": "value"}).to_json(orient="records"))
    ema_10 = json.loads(data_df.dropna(subset=['ema_10']).rename(columns={"ema_10": "value"}).to_json(orient="records"))
    ema_20 = json.loads(data_df.dropna(subset=['ema_20']).rename(columns={"ema_20": "value"}).to_json(orient="records"))
    ema_50 = json.loads(data_df.dropna(subset=['ema_50']).rename(columns={"ema_50": "value"}).to_json(orient="records"))
    
    sma_5 = json.loads(data_df.dropna(subset=['sma_5']).rename(columns={"sma_5": "value"}).to_json(orient="records"))
    sma_20 = json.loads(data_df.dropna(subset=['sma_20']).rename(columns={"sma_20": "value"}).to_json(orient="records"))
    sma_40 = json.loads(data_df.dropna(subset=['sma_40']).rename(columns={"sma_40": "value"}).to_json(orient="records"))
    

    rsi = json.loads(data_df.dropna(subset=['rsi']).rename(columns={"rsi": "value"}).to_json(orient="records"))
    macd = json.loads(data_df.dropna(subset=['macd']).rename(columns={"macd": "value"}).to_json(orient="records"))
    macd_signal = json.loads(data_df.dropna(subset=['macd_signal']).rename(columns={"macd_signal": "value"}).to_json(orient="records"))
    macd_histogram = json.loads(data_df.dropna(subset=['macd_histogram']).rename(columns={"macd_histogram": "value"}).to_json(orient="records"))
    stochastic_k = json.loads(data_df.dropna(subset=['stochastic_k']).rename(columns={"stochastic_k": "value"}).to_json(orient="records"))
    stochastic_d = json.loads(data_df.dropna(subset=['stochastic_d']).rename(columns={"stochastic_d": "value"}).to_json(orient="records"))
    mfi = json.loads(data_df.dropna(subset=['mfi']).rename(columns={"mfi": "value"}).to_json(orient="records"))

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
            "height": 150,  # MACD 차트 높이 설정
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
            "height": 150,  # Stocastic 차트 높이 설정
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
        },
        {
            "height": 150,  # MFI 차트 높이 설정
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
                "text": 'Mfi'
            }
        }
    ]

    seriesCandlestickChart = [
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
    
    # Bollinger Band
    if "bollinger" in selected_indicators:
        seriesCandlestickChart.extend([
            {
                "type": 'Line',
                "data": bollinger_band_upper,
                "options": {
                    "color": 'rgba(0, 0, 0, 1)',
                    "lineWidth": 0.5,
                    "priceScaleId": "right",
                    "lastValueVisible": False,
                    "priceLineVisible": False,
                },
            },
            {
            "type": 'Line',
            "data": bollinger_band_middle,  # 중단 밴드 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 0.5,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
                },
            },
            {
                "type": 'Line',
                "data": bollinger_band_lower,
                "options": {
                    "color": 'rgba(0, 0, 0, 1)',
                    "lineWidth": 0.5,
                    "priceScaleId": "right",
                    "lastValueVisible": False,
                    "priceLineVisible": False,
                },
            },
        ])
        
        # EMA 10
    if "ema_10" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_10,
            "options": {
                "color": 'rgba(255, 0, 0, 1)',
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })
        
                # EMA 20
    if "ema_20" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_20,
            "options": {
                "color": 'rgba(0, 255, 0, 1)',  # 초록색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })

        # EMA 50
    if "ema_50" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_50,
            "options": {
                "color": 'rgba(0, 0, 255, 1)',  # 파란색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })
        
        # EMA 60
    if "ema_60" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_60,
            "options": {
                "color": 'rgba(0, 170, 170, 1)', #청록색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        })

        # sma_5
    if "sma_5" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": sma_5,
            "options": {
                "color": 'purple', #청록색
                "lineWidth": 1.5,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        })
        
        # sma_20
    if "sma_20" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": sma_20,
            "options": {
                "color": 'teal', #청록색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        })
        
        # sma_40
    if "sma_40" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": sma_40,
            "options": {
                "color": 'orange', #청록색
                "lineWidth": 1.5,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        })                
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
                "color": 'rgba(0, 150, 255, 1)', #파란색
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line',
            "data": macd_signal, 
            "options": {
                "color": 'rgba(255, 0, 0, 1)', #빨간색
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
                "color": 'rgba(0, 150, 255, 1)', #파란색
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line', 
            "data": stochastic_d, 
            "options": {
                "color": 'rgba(255, 0, 0, 1)', #빨간색
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
    ]

    seriesMfiChart = [
        {
            "type": 'Line', 
            "data": mfi, 
            "options": {
                "color": 'rgba(0, 150, 255, 1)', #파란색 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line',
            "data": [{"time": row["time"], "value": 80} for row in mfi],  # 과매도 라인
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
            "data": [{"time": row["time"], "value": 20} for row in mfi],  # 과매수 라인
            "options": {
                "color": 'rgba(200, 0, 0, 0.5)',  # 빨간색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
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
        {
            "chart": chartMultipaneOptions[5],
            "series": seriesMfiChart
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
        elif entry.get('trading_logic') == 'stochastic_trading':
            entry['trading_logic'] = '스토캐스틱'
        elif entry.get('trading_logic') == 'macd_trading':
            entry['trading_logic'] = 'macd 확인'
        elif entry.get('trading_logic') == 'rsi+mfi':
            entry['trading_logic'] = 'rsi+mfi'
        elif entry.get('trading_logic') == 'ema_breakout_trading':
            entry['trading_logic'] = '지수이동평균선 확인'
        elif entry.get('trading_logic') == 'bollinger_band_trading':
            entry['trading_logic'] = '볼린저밴드 매매'
        elif entry.get('trading_logic') == 'bollinger+ema':
            entry['trading_logic'] = '볼린저+지수이동평균선'
        elif entry.get('trading_logic') == 'ema_breakout_trading2':
            entry['trading_logic'] = '지수이동평균선 확인2'
        elif entry.get('trading_logic') == 'trend_entry_trading':
            entry['trading_logic'] = '상승추세형 매수'
        elif entry.get('trading_logic') == 'bottom_rebound_trading':
            entry['trading_logic'] =  '저점반등형 매수'
        elif entry.get('trading_logic') == 'top_reversal_sell_trading':
            entry['trading_logic'] =  '고점반락형 매도'
        elif entry.get('trading_logic') == 'downtrend_sell_trading':
            entry['trading_logic'] =  '하락추세형 매도'
        elif entry.get('trading_logic') == 'sma_breakout_trading':
            entry['trading_logic'] =  '단순이동평균'
        elif entry.get('trading_logic') == 'ema_breakout_trading3':
            entry['trading_logic'] =  '지수이동평균선 확인3'                                                     
            
def login_page():
    """
    로그인 페이지: 사용자 로그인 및 세션 상태 관리
    """
    st.title("🔑 로그인 페이지")

    # 사용자 입력 받기
    username = st.text_input("아이디", key="username")
    password = st.text_input("비밀번호", type="password", key="password")
    
    # 간단한 사용자 검증 (실제 서비스에서는 DB 연동 필요)
    if st.button("로그인"):
        # 로그인 정보 조회
        result = list(UserInfo.scan(
            filter_condition=((UserInfo.id == username) & (UserInfo.password == password))
        ))
        
        if len(result) > 0:
            st.session_state["authenticated"] = True
            st.query_params = {"page" : "main", "login": "true"}
            st.rerun()  # 로그인 후 페이지 새로고침
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        
        
def setup_sidebar(sql_executer):
    """
    공통적으로 사용할 사이드바 UI를 설정하는 함수
    """
    
    st.sidebar.header("Simulation Settings")

    id = 'id2'

    # AutoTradingBot 및 SQLExecutor 객체 생성
    sql_executor = SQLExecutor()
    auto_trading_stock = AutoTradingBot(id=id, virtual=False)
    
    current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    # 사용자 입력
    # user_name = st.sidebar.text_input("User Name", value="홍석문")
    start_date = st.sidebar.date_input("Start Date", value=date(2023, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=current_date_kst)
    target_trade_value_krw = st.sidebar.number_input("Target Trade Value (KRW)", value=1000000, step=100000)

    result = list(StockSymbol.scan(
        filter_condition=((StockSymbol.type == 'kospi200') | (StockSymbol.type == 'kosdaq150') | (StockSymbol.type == 'NASDAQ') | (StockSymbol.type == 'etf') )
    ))
    
    type_order = {
    'kospi200': 1,
    'NASDAQ': 0,
    'kosdaq150': 2,
    'etf': 3
    }#type 순서

    #종목을 type 순서로 정렬한 후 이름순으로 정렬
    sorted_items = sorted(
    result,
    key=lambda x: (
        type_order.get(getattr(x, 'type', ''),99), 
        getattr(x, 'symbol_name', ''))
    )
    

    # Dropdown 메뉴를 통해 데이터 선택
    symbol_options = {
        # "삼성전자": "352820",
        # "대한항공": "003490",
    }

    for stock in sorted_items:
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
    
    #mode
    ohlc_mode_checkbox = st.sidebar.checkbox("차트 연결 모드")  # True / False 반환
    ohlc_mode = "continuous" if ohlc_mode_checkbox else "default"
    
        # ✅ 실제 투자 조건 체크박스
    real_trading_enabled = st.sidebar.checkbox("💰 실제 투자자본 설정")
    real_trading_yn = "Y" if real_trading_enabled else "N"

    # ✅ 매수 퍼센트 입력
    initial_capital = None
    if real_trading_yn == "Y":
        initial_capital = st.sidebar.number_input("💰 초기 투자 자본 (KRW)", min_value=0, value=10_000_000, step=1_000_000)
        
    #✅ rsi 조건값 입력
    rsi_buy_threshold = st.sidebar.number_input("📉 RSI 매수 임계값", min_value=0, max_value=100, value=35, step=1)
    rsi_sell_threshold = st.sidebar.number_input("📈 RSI 매도 임계값", min_value=0, max_value=100, value=70, step=1)
    rsi_period = st.sidebar.number_input("📈 RSI 기간 설정", min_value=0, max_value=100, value=25, step=1)
    
    # 📌 Streamlit 체크박스 입력
    st.sidebar.subheader("📊 차트 지표 선택")
    # 체크박스로 사용자 선택 받기
    selected_indicators = []
    if st.sidebar.checkbox("EMA 10", value=True):
        selected_indicators.append("ema_10")
    if st.sidebar.checkbox("EMA 20", value=True):
        selected_indicators.append("ema_20")
    if st.sidebar.checkbox("EMA 50", value=True):
        selected_indicators.append("ema_50")        
    if st.sidebar.checkbox("EMA 60", value=True):
        selected_indicators.append("ema_60")
    if st.sidebar.checkbox("SMA 5", value=False):
        selected_indicators.append("sma_5")
    if st.sidebar.checkbox("SMA 20", value=False):
        selected_indicators.append("sma_20")
    if st.sidebar.checkbox("SMA 40", value=False):
        selected_indicators.append("sma_40")                
    if st.sidebar.checkbox("bollinger band", value=False):
        selected_indicators.append("bollinger")
        
    # ✅ 설정 값을 딕셔너리 형태로 반환
    return {
        "id": id,
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
        "rsi_sell_threshold" : rsi_sell_threshold,
        "rsi_period" : rsi_period,
        "selected_indicators" : selected_indicators,
        "initial_capital" : initial_capital
    }
    
def setup_my_page():
    """
    마이페이지 설정 탭: 사용자 맞춤 설정 저장
    """
    st.header("🛠 마이페이지 설정")

    # AutoTradingBot, trading_logic 및 SQLExecutor 객체 생성
    id = "id1"  # 사용자 이름 (고정값)
    auto_trading_stock = AutoTradingBot(id=id, virtual=False)
    
    current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()

    start_date = st.date_input("📅 Start Date", value=date(2023, 1, 1))
    end_date = st.date_input("📅 End Date", value=current_date_kst)
    
    #target_trade_value_krw = st.number_input("💰 Target Trade Value (KRW)", value=2000000, step=100000)
    st.subheader("💰 매수 금액 설정 방식")

    target_method = st.radio(
        "매수 금액을 어떻게 설정할까요?",
        ["직접 입력", "자본 비율 (%)"],
        index=0
    )

    if target_method == "직접 입력":
        target_trade_value_krw = st.number_input("🎯 목표 매수 금액 (KRW)", min_value=10000, step=10000, value=1000000)
        target_trade_value_ratio = None
    else:
        target_trade_value_ratio = st.slider("💡 초기 자본 대비 매수 비율 (%)", 1, 100, 20) #마우스 커서로 왔다갔다 하는 기능
        target_trade_value_krw = None  # 실제 시뮬 루프에서 매일 계산
    # ✅ 실제 투자 조건 체크박스
    real_trading_enabled = st.checkbox("💰 실제 투자자본 설정", key="real_trading_enabled")
    real_trading_yn = "Y" if real_trading_enabled else "N"

    # ✅ 매수 퍼센트 입력
    initial_capital = None
    if real_trading_yn == "Y":
        initial_capital = st.number_input("💰 초기 투자 자본 (KRW)", min_value=0, value=10_000_000, step=1_000_000, key="initial_capital")
        
    # ✅ DB에서 종목 리스트 가져오기
    result = list(StockSymbol.scan(
        filter_condition=((StockSymbol.type == 'kospi200') | (StockSymbol.type == 'kosdaq150'))
    ))
    
    type_order = {
    'kospi200': 1,
    #'NASDAQ': 0,
    'kosdaq150': 2
    }#type 순서

    #종목을 type 순서로 정렬한 후 이름순으로 정렬
    sorted_items = sorted(
    result,
    key=lambda x: (
        type_order.get(getattr(x, 'type', ''),99), 
        getattr(x, 'symbol_name', ''))
    )

    symbol_options = {row.symbol_name: row.symbol for row in sorted_items}
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
        
    use_take_profit = st.checkbox("익절 조건 사용", value=False)
    take_profit_ratio = st.number_input("익절 기준 (%)", value=5.0, min_value=0.0)

    use_stop_loss = st.checkbox("손절 조건 사용", value=False)
    stop_loss_ratio = st.number_input("손절 기준 (%)", value=5.0, min_value=0.0)        

    #✅ rsi 조건값 입력
    st.subheader("🎯 RSI 조건값 설정")
    rsi_buy_threshold = st.number_input("📉 RSI 매수 임계값", min_value=0, max_value=100, value=35, step=1, key = 'rsi_buy_threshold')
    rsi_sell_threshold = st.number_input("📈 RSI 매도 임계값", min_value=0, max_value=100, value=70, step=1, key = 'rsi_sell_threshold')
    rsi_period = st.number_input("📈 RSI 기간 설정", min_value=0, max_value=100, value=25, step=1, key = 'rsi_period')

    # ✅ 설정 저장 버튼
    if st.button("✅ 설정 저장"):
        st.session_state["my_page_settings"] = {
            "id": id,
            "start_date": start_date,
            "end_date": end_date,
            "target_trade_value_krw": target_trade_value_krw,
            "target_trade_value_ratio": target_trade_value_ratio,
            "selected_stocks": selected_stocks, #이름만
            "selected_symbols": selected_symbols, #이름+코드(key,value)
            "interval": interval,
            "selected_buyTrading_logic": selected_buyTrading_logic,
            "selected_sellTrading_logic": selected_sellTrading_logic,
            "buy_condition_yn": buy_condition_yn,
            "buy_percentage": buy_percentage,
            "initial_capital": initial_capital,
            "rsi_buy_threshold" : rsi_buy_threshold,
            "rsi_sell_threshold" : rsi_sell_threshold,
            "rsi_period" : rsi_period,
            "use_take_profit": use_take_profit,
            "take_profit_ratio": take_profit_ratio,
            "use_stop_loss": use_stop_loss,
            "stop_loss_ratio" : stop_loss_ratio 
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
    
    st.title("🏠 메인 페이지")
    
    if st.button("로그아웃"):
        st.session_state["authenticated"] = False
        st.query_params = {"page" : "login", "login": "false"}
        st.rerun()  # 로그아웃 후 페이지 새로고침
        
    # ✅ 공통 사이드바 설정 함수 실행 후 값 가져오기
    sidebar_settings = setup_sidebar(sql_executor)
    
    # 탭 생성
    tabs = st.tabs(["🏠 Bot transaction history", "📈 Simulation Graph", "📊 KOSPI200 Simulation", "🛠 Settings", "📈Auto Trading Bot Balance"])

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
        AgGrid(
            df,
            editable=True,  # 셀 편집 가능
            sortable=True,  # 정렬 가능
            filter=True,    # 필터링 가능
            resizable=True, # 크기 조절 가능
            theme='streamlit',   # 테마 변경 가능 ('light', 'dark', 'blue', 등)
            fit_columns_on_grid_load=True  # 열 너비 자동 조정
        )

    # -- 시뮬레이션 결과를 저장할 세션 상태 초기화 --
    if "simulation_result" not in st.session_state:
        st.session_state.simulation_result = None
    
    with tabs[1]:
        st.header("📈 종목 시뮬레이션")
        
        if st.sidebar.button("개별 종목 시뮬레이션 실행", key = 'simulation_button'):
            auto_trading_stock = AutoTradingBot(id=sidebar_settings["id"], virtual=False)
            
            
            with st.container():
                st.write(f"📊 {sidebar_settings['selected_stock']} 시뮬레이션 실행 중...")
                
                #시뮬레이션 실행
                data_df, trading_history, trade_reasons = auto_trading_stock.simulate_trading(
                    symbol=sidebar_settings["symbol"],
                    start_date=sidebar_settings["start_date"],
                    end_date=sidebar_settings["end_date"],
                    target_trade_value_krw=sidebar_settings["target_trade_value_krw"],
                    buy_trading_logic=sidebar_settings["buy_trading_logic"],
                    sell_trading_logic=sidebar_settings["sell_trading_logic"],
                    interval=sidebar_settings["interval"],
                    buy_percentage=sidebar_settings["buy_percentage"],
                    ohlc_mode = sidebar_settings["ohlc_mode"],
                    rsi_buy_threshold= sidebar_settings['rsi_buy_threshold'],
                    rsi_sell_threshold= sidebar_settings['rsi_sell_threshold'],
                    rsi_period= sidebar_settings['rsi_period'],
                    initial_capital = sidebar_settings['initial_capital']
                    
                )
                # 시뮬레이션 결과를 session_state에 저장
                st.session_state.simulation_result = {
                    "data_df": data_df,
                    "trading_history": trading_history,
                    "trade_reasons": trade_reasons
                }
    
        # -- 세션 상태에 시뮬레이션 결과가 있다면 이를 표시 --
        if st.session_state.simulation_result is not None:
            result = st.session_state.simulation_result
            data_df = result["data_df"]
            trading_history = result["trading_history"]
            trade_reasons = result["trade_reasons"]
            
            
            # CSV 다운로드 버튼 - trade_reasons DataFrame 생성 후 다운로드
            if trade_reasons:
                df_trade = pd.DataFrame(trade_reasons)
            else:
                st.warning("🚨 거래 내역이 없습니다.")
                df_trade = pd.DataFrame()
            
            st.subheader("📥 데이터 다운로드")
            csv_buffer = io.StringIO()
            df_trade.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📄 CSV 파일 다운로드",
                data=csv_buffer.getvalue(),
                file_name="trade_reasons.csv",
                mime="text/csv"
            )
            
            selected_indicators = sidebar_settings['selected_indicators'] # 차트 지표 선택 리스트
            # TradingView 차트 그리기
            draw_lightweight_chart(data_df, selected_indicators)
            
            # -- Trading History 처리 --
            if not trading_history:
                st.write("No trading history available.")
            else:
                # 거래 내역을 DataFrame으로 변환
                history_df = pd.DataFrame([trading_history])
        
                # 실현/미실현 수익률에 % 포맷 적용
                for column in ["realized_roi", "unrealized_roi"]:
                    if column in history_df.columns:
                        history_df[column] = history_df[column].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)
                        
                # symbol 변수 설정 (예시; 필요시 수정)
                history_df["symbol"] = sidebar_settings['selected_stock']
        
                reorder_columns = [
                    "symbol", "average_price",
                    "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi", "total_cost",
                    "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity", "history", "created_at"
                ]
                history_df = history_df[[col for col in reorder_columns if col in history_df.columns]]
        
                history_df_transposed = history_df.transpose().reset_index()
                history_df_transposed.columns = ["Field", "Value"]
        
                st.subheader("📊 Trading History Summary")
                st.dataframe(history_df_transposed, use_container_width=True)
                
                if "history" in trading_history and isinstance(trading_history["history"], list) and trading_history["history"]:
                    rename_tradingLogic(trading_history["history"])  # 필요 시 로직명 변환
                    trade_history_df = pd.DataFrame(trading_history["history"])
        
                    st.subheader("📋 Detailed Trade History")
                    st.dataframe(trade_history_df, use_container_width=True)
                else:
                    st.write("No detailed trade history found.")
        else:
            st.info("먼저 시뮬레이션을 실행해주세요.")
                    

    # with tabs[2]:
    #     st.header("📊 데이터 분석 페이지")
        
    #     # 데이터
    #     data = sns.load_dataset('penguins')

    #     # 히스토그램
    #     fig, ax = plt.subplots(figsize=(10, 6))
    #     sns.histplot(data, x='flipper_length_mm', hue='species', multiple='stack', ax=ax)
    #     ax.set_title("Seaborn 히스토그램")
    #     st.pyplot(fig)
        
        #새로 추가된 코스피 200 시뮬레이션 탭
    # with tabs[3]:
    #     st.header("📊 선택한 종목 시뮬레이션 결과")

    #     # ✅ 시뮬레이션 실행 버튼
    #     if st.button("선택 종목 시뮬레이션 실행"):
            
    #         my_page_settings = st.session_state["my_page_settings"]
    #         st.write("🔄 선택한 종목에 대해 시뮬레이션을 실행합니다.")

    #         # ✅ 진행률 바 추가
    #         progress_bar = st.progress(0)
    #         progress_text = st.empty()  # 진행 상태 표시

    #         all_trading_results = []
    #         failed_stocks = []
    #         total_stocks = len(my_page_settings["selected_symbols"])
            
    #         for i, (stock_name, symbol) in enumerate(my_page_settings["selected_symbols"].items()):
    #             try:
    #                 with st.spinner(f"📊 {stock_name} ({i+1}/{total_stocks}) 시뮬레이션 실행 중..."):
    #                     auto_trading_stock = AutoTradingBot(id=my_page_settings["id"], virtual=False)

    #                     _, trading_history, trade_reasons = auto_trading_stock.simulate_trading(
    #                         symbol=symbol,
    #                         start_date=my_page_settings["start_date"],
    #                         end_date=my_page_settings["end_date"],
    #                         target_trade_value_krw=my_page_settings["target_trade_value_krw"],
    #                         buy_trading_logic=my_page_settings["selected_buyTrading_logic"],
    #                         sell_trading_logic=my_page_settings["selected_sellTrading_logic"],
    #                         interval=my_page_settings["interval"],
    #                         buy_percentage=my_page_settings["buy_percentage"],
    #                         initial_capital= my_page_settings['initial_capital'],
    #                         rsi_buy_threshold = my_page_settings['rsi_buy_threshold'],
    #                         rsi_sell_threshold = my_page_settings['rsi_sell_threshold'],
    #                         rsi_period = my_page_settings['rsi_period']
    #                     )

    #                     if trading_history:
    #                         trading_history["symbol"] = stock_name
    #                         all_trading_results.append(trading_history)

    #                 # ✅ 진행률 업데이트
    #                 progress = (i + 1) / total_stocks
    #                 progress_bar.progress(progress)
    #                 progress_text.text(f"{int(progress * 100)}% 완료 ({i+1}/{total_stocks})")

    #             except Exception as e:
    #                 st.write(f"⚠️ {stock_name} 시뮬레이션 실패: {str(e)}")
    #                 failed_stocks.append(stock_name)

    #         st.success("✅ 선택 종목 시뮬레이션 완료!")
            
    #         # ✅ 시뮬레이션 결과를 `st.session_state`에 저장!(페이지 리셋해도 계속 저장하기 위함)
    #         st.session_state["kospi200_trading_results"] = all_trading_results

    #         # ✅ 시뮬레이션 결과를 `st.session_state`에서 가져와 사용
    #         if st.session_state["kospi200_trading_results"]:
    #             df_results = pd.DataFrame(st.session_state["kospi200_trading_results"])
                
    #             # 원하는 컬럼 순서 지정
    #             reorder_columns = [
    #                 "symbol", "average_price",
    #                 "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi",
    #                 "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity", "created_at"
    #             ]
                
    #             # ✅ 데이터가 있는 컬럼만 유지
    #             df_results = df_results[[col for col in reorder_columns if col in df_results.columns]]

    #             df_results["buy_dates"] = df_results["buy_dates"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    #             df_results["sell_dates"] = df_results["sell_dates"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    #             #df_results["history"] = None  # 혹은 df_results.drop(columns=["history"], inplace=True)
                
    #             # 수익률 컬럼이 존재하면 % 형식 변환
    #             for col in ["realized_roi", "unrealized_roi"]:
    #                 if col in df_results.columns:
    #                     df_results[col] = df_results[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)

    #             # ✅ 전체 합계 계산(총 실현 손익/미실현 손익)
    #             total_realized_pnl = df_results["realized_pnl"].sum()
    #             total_unrealized_pnl = df_results["unrealized_pnl"].sum()
                
    #             # ✅ 평균 실현 손익률 & 평균 미실현 손익률 (빈 값 제외)
    #             avg_realized_roi = df_results["realized_roi"].replace("%", "", regex=True).astype(float).mean()
    #             avg_unrealized_roi = df_results["unrealized_roi"].replace("%", "", regex=True).astype(float).mean()
                
    #             initial_capital = my_page_settings['initial_capital']
    #             # ✅ 초기 자본 대비 평균 손익률 계산 (초기 자본이 0이 아닐 경우에만 계산)
    #             if initial_capital is not None and initial_capital > 0:
    #                 avg_realized_roi_per_capital = (total_realized_pnl / initial_capital) * 100
    #                 avg_total_roi_per_capital = ((total_realized_pnl + total_unrealized_pnl) / initial_capital) * 100
    #             else:
    #                 avg_realized_roi_per_capital = None
    #                 avg_total_roi_per_capital = None                

    #             # ✅ 손익 요약 정보 표시
    #             st.subheader("📊 전체 종목 손익 요약")
    #             st.write(f"**💰 총 실현 손익:** {total_realized_pnl:,.2f} KRW")
    #             st.write(f"**📈 총 미실현 손익:** {total_unrealized_pnl:,.2f} KRW")
    #             st.write(f"**📊 평균 실현 손익률:** {avg_realized_roi:.2f}% KRW")
    #             st.write(f"**📉 평균 총 손익률:** {avg_unrealized_roi:.2f}% KRW")
    #             # ✅ 초기 자본 대비 평균 손익률 추가 표시
    #             if initial_capital is not None:
    #                 st.write(f"**📊 초기 자본 대비 평균 실현 손익률:** {avg_realized_roi_per_capital:.2f}%")
    #                 st.write(f"**📉 초기 자본 대비 평균 총 손익률:** {avg_total_roi_per_capital:.2f}%")
                
    #             # ✅ 개별 종목별 결과 표시
    #             st.subheader("📋 종목별 시뮬레이션 결과")
    #             AgGrid(
    #                 df_results,
    #                 editable=True,
    #                 sortable=True,
    #                 filter=True,
    #                 resizable=True,
    #                 theme='streamlit',
    #                 fit_columns_on_grid_load=True,
    #                 update_mode=GridUpdateMode.NO_UPDATE  # ✅ 핵심! 클릭해도 아무 일 없음
    #             )

    #             # ✅ 실패한 종목이 있다면 표시
    #             if failed_stocks:
    #                 st.warning(f"⚠️ 시뮬레이션 실패 종목 ({len(failed_stocks)}개): {', '.join(failed_stocks)}")

    #         else:
    #             st.write("⚠️ 시뮬레이션 결과가 없습니다.")
    
    # with tabs[3]:            
    #     if st.button("✅ 시뮬레이션 실행"):
            
    #         my_settings = st.session_state["my_page_settings"]
    #         symbols = my_settings["selected_symbols"]
    #         interval = my_settings["interval"]
    #         start = my_settings["start_date"]
    #         end = my_settings["end_date"]                
    #         auto_trading_stock = AutoTradingBot(id=my_settings["id"], virtual=False)
    #         rsi_period = my_settings['rsi_period']
            
    #         df_dict = {}
    #         ohlc_dict = {}
            
    #         for stock_name, symbol in symbols.items():
                
    #             full_start = start - timedelta(days=180)
    #             ohlc_data = auto_trading_stock._get_ohlc(symbol, full_start, end, interval)

    #             # DataFrame 변환
    #             timestamps = [c.time for c in ohlc_data]
    #             ohlc = [[c.time, float(c.open), float(c.high), float(c.low), float(c.close), float(c.volume)] for c in ohlc_data]
    #             df = pd.DataFrame(ohlc, columns=["Time", "Open", "High", "Low", "Close", "Volume"], index=pd.DatetimeIndex(timestamps))
    #             df.index = df.index.tz_localize(None)
    #             indicator = TechnicalIndicator()
    #             # 지표 계산
    #             #ema
    #             df = indicator.cal_ema_df(df, 10)
    #             df = indicator.cal_ema_df(df, 20)
    #             df = indicator.cal_ema_df(df, 50)
    #             df = indicator.cal_ema_df(df, 60)
                
    #             #sma
    #             df = indicator.cal_sma_df(df, 5)
    #             df = indicator.cal_sma_df(df, 20)
    #             df = indicator.cal_sma_df(df, 40)

    #             df = indicator.cal_rsi_df(df, rsi_period)
    #             df = indicator.cal_macd_df(df)
    #             df = indicator.cal_stochastic_df(df)
    #             df = indicator.cal_mfi_df(df)
    #             df_dict[symbol] = df
    #             ohlc_dict[symbol] = ohlc_data

    #         # 초기 자본 상태
    #         global_state = {
    #             'initial_capital': my_settings["initial_capital"],
    #             'realized_pnl': 0,
    #             'unrealized_pnl': 0,
    #             'realized_roi': 0,
    #             'unrealized_roi': 0,
    #             'history': []
    #         }

    #         # 종목별 보유 상태
    #         holding_state = {
    #             symbol: {
    #                 'total_quantity': 0,
    #                 'average_price': 0,
    #                 'total_cost': 0,
    #                 'buy_count': 0,
    #                 'sell_count': 0,
    #                 'buy_dates': [],
    #                 'sell_dates': [],
    #                 'unrealized_pnl': 0,
    #                 'unrealized_roi': 0
    #             }
    #             for symbol in symbols.values()
    #         }

    #         st.success("✅ 지표 계산 완료. 시뮬레이션을 시작합니다...")

    #         date_range = pd.date_range(start, end)
    #         all_results = []
        
    #         total_tasks = len(date_range) * len(symbols)
    #         current_task = 0
    #         progress_bar = st.progress(0)
    #         progress_text = st.empty()
    #         all_results = []

    #         for current_date in date_range:
    #             for stock_name, symbol in symbols.items():
    #                 try:
    #                     df = df_dict[symbol]
    #                     ohlc_data = ohlc_dict[symbol]
    #                     state = holding_state[symbol]

    #                     trading_history = auto_trading_stock.whole_simulate_trading(
    #                         symbol=symbol,
    #                         end_date=current_date,
    #                         df=df,
    #                         ohlc_data=ohlc_data,
    #                         target_trade_value_krw=my_settings["target_trade_value_krw"],
    #                         buy_trading_logic=my_settings["selected_buyTrading_logic"],
    #                         sell_trading_logic=my_settings["selected_sellTrading_logic"],
    #                         interval=interval,
    #                         buy_percentage=my_settings["buy_percentage"],
    #                         initial_capital=global_state["initial_capital"],
    #                         rsi_buy_threshold=my_settings["rsi_buy_threshold"],
    #                         rsi_sell_threshold=my_settings["rsi_sell_threshold"],
    #                         total_quantity=state['total_quantity']  # ✅ 종목별 보유 수량 전달
    #                     )

    #                     trading_history.update({
    #                         "symbol": stock_name,
    #                         "sim_date": current_date.strftime('%Y-%m-%d'),
    #                         "buy_count": state["buy_count"],
    #                         "sell_count": state["sell_count"],
    #                         "buy_dates": state["buy_dates"],
    #                         "sell_dates": state["sell_dates"],
    #                         "total_quantity": state["total_quantity"]
    #                     })

    #                     all_results.append(trading_history.copy())
    #                     global_state = trading_history

    #                 except Exception as e:
    #                     st.warning(f"⚠️ {stock_name} ({current_date.date()}) 실패: {e}")

    #                 current_task += 1
    #                 progress = current_task / total_tasks
    #                 progress_bar.progress(progress)
    #                 progress_text.text(f"📊 진행 중: {current_task}/{total_tasks} ({progress*100:.1f}%)")

    #         st.success("✅ 시뮬레이션 완료!")

    #         if all_results:
    #             df_results = pd.DataFrame(all_results)

    #             reorder_columns = [
    #                 "symbol", "average_price",
    #                 "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi",
    #                 "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity", "created_at"
    #             ]
    #             df_results = df_results[[col for col in reorder_columns if col in df_results.columns]]

    #             df_results["buy_dates"] = df_results["buy_dates"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    #             df_results["sell_dates"] = df_results["sell_dates"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    #             for col in ["realized_roi", "unrealized_roi"]:
    #                 if col in df_results.columns:
    #                     df_results[col] = df_results[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)

    #             total_realized_pnl = df_results["realized_pnl"].sum()
    #             total_unrealized_pnl = df_results["unrealized_pnl"].sum()

    #             avg_realized_roi = df_results["realized_roi"].replace("%", "", regex=True).astype(float).mean()
    #             avg_unrealized_roi = df_results["unrealized_roi"].replace("%", "", regex=True).astype(float).mean()

    #             initial_capital = my_settings["initial_capital"]
    #             if initial_capital:
    #                 avg_realized_roi_per_capital = (total_realized_pnl / initial_capital) * 100
    #                 avg_total_roi_per_capital = ((total_realized_pnl + total_unrealized_pnl) / initial_capital) * 100
    #             else:
    #                 avg_realized_roi_per_capital = None
    #                 avg_total_roi_per_capital = None

    #             st.subheader("📊 전체 종목 손익 요약")
    #             st.write(f"**💰 총 실현 손익:** {total_realized_pnl:,.2f} KRW")
    #             st.write(f"**📈 총 미실현 손익:** {total_unrealized_pnl:,.2f} KRW")
    #             st.write(f"**📊 평균 실현 손익률:** {avg_realized_roi:.2f}%")
    #             st.write(f"**📉 평균 총 손익률:** {avg_unrealized_roi:.2f}%")
    #             if initial_capital:
    #                 st.write(f"**📊 초기 자본 대비 평균 실현 손익률:** {avg_realized_roi_per_capital:.2f}%")
    #                 st.write(f"**📉 초기 자본 대비 평균 총 손익률:** {avg_total_roi_per_capital:.2f}%")

    #             st.subheader("📋 종목별 시뮬레이션 결과")
    #             AgGrid(
    #                 df_results,
    #                 editable=True,
    #                 sortable=True,
    #                 filter=True,
    #                 resizable=True,
    #                 theme='streamlit',
    #                 fit_columns_on_grid_load=True,
    #                 update_mode=GridUpdateMode.NO_UPDATE
    #             )

    #         else:
    #             st.write("⚠️ 시뮬레이션 결과가 없습니다.")
    
    with tabs[2]:
        if st.button("📊 1. OHLC + 지표 사전 계산"):
            my = st.session_state["my_page_settings"]

            precomputed_df_dict = {}
            precomputed_ohlc_dict = {}
            valid_symbols = {}
            failed_indicator_symbols = []

            start_date = my["start_date"] - timedelta(days=180)
            end_date = my["end_date"]
            interval = my["interval"]

            with st.spinner("📈 전체 종목 OHLC 및 지표 계산 중..."):
                for stock_name, symbol in my["selected_symbols"].items():
                    try:
                        auto_trading_stock = AutoTradingBot(id=my["id"], virtual=False)

                        # ✅ OHLC 데이터 가져오기
                        ohlc_data = auto_trading_stock._get_ohlc(symbol, start_date, end_date, interval)
                        precomputed_ohlc_dict[symbol] = ohlc_data

                        # ✅ OHLC → DataFrame 변환
                        timestamps = [c.time for c in ohlc_data]
                        ohlc = [
                            [c.time, float(c.open), float(c.high), float(c.low), float(c.close), float(c.volume)]
                            for c in ohlc_data
                        ]
                        df = pd.DataFrame(ohlc, columns=["Time", "Open", "High", "Low", "Close", "Volume"], index=pd.DatetimeIndex(timestamps))
                        df.index = df.index.tz_localize(None)
                        indicator = TechnicalIndicator()
                        rsi_period = my['rsi_period']
                        # ✅ 지표 계산
                        #ema
                        df = indicator.cal_ema_df(df, 10)
                        df = indicator.cal_ema_df(df, 20)
                        df = indicator.cal_ema_df(df, 50)
                        df = indicator.cal_ema_df(df, 60)
                        
                        #sma
                        df = indicator.cal_sma_df(df, 5)
                        df = indicator.cal_sma_df(df, 20)
                        df = indicator.cal_sma_df(df, 40)

                        df = indicator.cal_rsi_df(df, rsi_period)
                        df = indicator.cal_macd_df(df)
                        df = indicator.cal_stochastic_df(df)
                        df = indicator.cal_mfi_df(df)

                        # 유효한 종목만 저장
                        valid_symbols[stock_name] = symbol
                        precomputed_df_dict[symbol] = df
                        precomputed_ohlc_dict[symbol] = ohlc_data

                    except Exception as e:
                        st.warning(f"⚠️ {stock_name} 지표 계산 실패: {e}")
                        failed_indicator_symbols.append(stock_name)

            # ✅ 세션 상태에 저장
            my["selected_symbols"] = valid_symbols
            my["precomputed_df_dict"] = precomputed_df_dict
            my["precomputed_ohlc_dict"] = precomputed_ohlc_dict

            st.success("✅ 모든 종목의 지표 계산 완료 및 저장됨!")
            
        if st.button("✅ 2. 시뮬레이션 실행"):
            my = st.session_state["my_page_settings"]
            symbols = my["selected_symbols"]
            target_ratio = my["target_trade_value_ratio"]  # None이면 직접 입력 방식
            
            date_range = pd.date_range(start=my["start_date"], end=my["end_date"])

            global_state = {
                'initial_capital': my["initial_capital"],
                'realized_pnl': 0,
                'buy_dates': [],
                'sell_dates': [],
            }

            holding_state = {
                symbol: {
                    'total_quantity': 0,
                    'average_price': 0,
                    'total_cost': 0,
                    'buy_count': 0,
                    'sell_count': 0,
                    'buy_dates': [],
                    'sell_dates': [],
                } for symbol in symbols.values()
            }

            results = []
            total_tasks = len(date_range) * len(symbols)
            #total_tasks = sum(len(my["precomputed_ohlc_dict"][symbol]) for symbol in symbols.values())
            task = 0

            progress_bar = st.progress(0)
            progress_text = st.empty()
            log_area = st.empty()
            failed_stocks = set()  # 중복 제거 자동 처리
            
            auto_trading_stock = AutoTradingBot(id=my["id"], virtual=False)
            
            start_date = pd.Timestamp(my["start_date"]).normalize()
            # 공통된 모든 날짜 모으기
            all_dates = set()
            for symbol in symbols.values():
                ohlc_data = my["precomputed_ohlc_dict"][symbol]
                dates = [pd.Timestamp(c.time).tz_localize(None).normalize() for c in ohlc_data]
                all_dates.update(d for d in dates if d >= start_date)

            date_range = sorted(list(all_dates))  # 날짜 정렬

            # ✅ 시뮬레이션 시작
            for current_date in date_range:
                for stock_name, symbol in symbols.items():
                    try:
                        df = my["precomputed_df_dict"][symbol]
                        ohlc_data = my["precomputed_ohlc_dict"][symbol]

                        # 해당 종목에 current_date가 실제 있는 날짜인지 확인
                        if not any(pd.Timestamp(c.time).tz_localize(None).normalize() == current_date for c in ohlc_data):
                            continue  # 종목이 그날 거래 안 했으면 스킵

                        # ✅ 날짜별 거래 금액 계산
                        if target_ratio is not None:
                            target_trade_value = int(global_state["initial_capital"] * target_ratio / 100)
                        else:
                            target_trade_value = my["target_trade_value_krw"]
                            
                        log_area.text(f"📊 [{current_date.date()}] {stock_name} 시뮬 중...")

                        trading_history = auto_trading_stock.whole_simulate_trading2(
                            symbol=symbol,
                            end_date=current_date,
                            df=df,
                            ohlc_data=ohlc_data,
                            target_trade_value_krw=target_trade_value,
                            buy_trading_logic=my["selected_buyTrading_logic"],
                            sell_trading_logic=my["selected_sellTrading_logic"],
                            interval=my["interval"],
                            buy_percentage=my["buy_percentage"],
                            initial_capital=global_state["initial_capital"],
                            rsi_buy_threshold=my["rsi_buy_threshold"],
                            rsi_sell_threshold=my["rsi_sell_threshold"],
                            global_state=global_state,
                            holding_state=holding_state[symbol],
                            use_take_profit=my["use_take_profit"],
                            take_profit_ratio=my["take_profit_ratio"],
                            use_stop_loss=my["use_stop_loss"],
                            stop_loss_ratio=my["stop_loss_ratio"]
                        )

                        if trading_history is None:
                            continue  # 데이터 부족하면 스킵

                        trading_history.update({
                            "symbol": stock_name,
                            "sim_date": current_date.strftime('%Y-%m-%d'),
                            "total_quantity": holding_state[symbol]["total_quantity"],
                            "average_price": holding_state[symbol]["average_price"],
                            "buy_count": holding_state[symbol]["buy_count"],
                            "sell_count": holding_state[symbol]["sell_count"],
                            "buy_dates": holding_state[symbol]["buy_dates"],
                            "sell_dates": holding_state[symbol]["sell_dates"]
                        })

                        global_state = trading_history.copy()
                        results.append(trading_history)

                        log_area.text(f"✅ [{current_date.date()}] {stock_name} 완료")

                    except Exception as e:
                        st.warning(f"⚠️ {stock_name} {current_date.date()} 실패: {e}")
                        failed_stocks.add(stock_name)

                    task += 1
                    progress = task / total_tasks
                    progress_bar.progress(progress)
                    progress_text.text(f"{int(progress * 100)}% 완료 ({task}/{total_tasks})")
                    
            signal_logs = []
            
            if results:
                df_results = pd.DataFrame(results)

                df_results["sim_date"] = pd.to_datetime(df_results["sim_date"])
                df_results = df_results.sort_values(by=["sim_date", "symbol"]).reset_index(drop=True)
                df_results["sim_date"] = df_results["sim_date"].dt.strftime("%Y-%m-%d")

                reorder_columns = [
                    "sim_date", "symbol", "initial_capital", "buy_count", "sell_count", "quantity",
                    "realized_pnl", "realized_roi", "unrealized_pnl", "unrealized_roi",
                    "total_quantity", "average_price"
                ]
                df_results = df_results[[col for col in reorder_columns if col in df_results.columns]]

                for col in ["realized_roi", "unrealized_roi"]:
                    if col in df_results.columns:
                        df_results[col] = df_results[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)

                st.subheader("📋 시뮬레이션 결과 테이블")
                st.dataframe(df_results, use_container_width=True)
                
                for row in results:
                    reasons = ", ".join(row.get("signal_reasons", []))
                    if row.get("buy_signal"):
                        signal_logs.append({
                            "sim_date": row["sim_date"],
                            "symbol": row["symbol"],
                            "signal": "BUY_SIGNAL",
                            "reason": reasons
                        })
                    if row.get("sell_signal"):
                        signal_logs.append({
                            "sim_date": row["sim_date"],
                            "symbol": row["symbol"],
                            "signal": "SELL_SIGNAL",
                            "reason": reasons
                        })

                if signal_logs:
                    df_signals = pd.DataFrame(signal_logs)
                    df_signals["sim_date"] = pd.to_datetime(df_signals["sim_date"])
                    df_signals = df_signals.sort_values(by=["sim_date", "symbol"]).reset_index(drop=True)
                    df_signals["sim_date"] = df_signals["sim_date"].dt.strftime("%Y-%m-%d")

                    st.subheader("📌 매매 신호가 발생한 날짜 (거래 여부와 무관)")
                    st.dataframe(df_signals, use_container_width=True)
                    
                    # ✅ 요약 통계 출력
                if not df_results.empty:
                    # 마지막 날짜의 unrealized_pnl/roi만 종목별로 추출
                    df_last_unrealized = df_results.sort_values("sim_date").groupby("symbol").last()
                    
                    total_realized_pnl = df_results["realized_pnl"].sum()
                    total_unrealized_pnl = df_last_unrealized["unrealized_pnl"].sum()

                    # '%' 제거 후 평균 계산
                    # avg_realized_roi = df_results["realized_roi"].replace("%", "", regex=True).astype(float).mean()
                    # avg_unrealized_roi = df_last_unrealized["unrealized_roi"].replace("%", "", regex=True).astype(float).mean()

                    initial_capital = my["initial_capital"]
                    if initial_capital and initial_capital > 0:
                        avg_realized_roi_per_capital = (total_realized_pnl / initial_capital) * 100
                        avg_total_roi_per_capital = ((total_realized_pnl + total_unrealized_pnl) / initial_capital) * 100
                    else:
                        avg_realized_roi_per_capital = None
                        avg_total_roi_per_capital = None

                    st.subheader("📊 전체 요약 통계")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("💰 총 실현 손익", f"{total_realized_pnl:,.0f} KRW")
                        st.metric("📈 총 미실현 손익", f"{total_unrealized_pnl:,.0f} KRW")
                        #st.metric("📊 평균 실현 손익률", f"{avg_realized_roi:.2f}%")
                        #st.metric("📉 평균 총 손익률", f"{avg_unrealized_roi:.2f}%")

                    with col2:
                        st.metric("📊 초기 자본 대비 평균 실현 손익률", f"{avg_realized_roi_per_capital:.2f}%" if avg_realized_roi_per_capital is not None else "N/A")
                        st.metric("📉 초기 자본 대비 평균 총 손익률", f"{avg_total_roi_per_capital:.2f}%" if avg_total_roi_per_capital is not None else "N/A")
                        
                            #             # ✅ 실패한 종목이 있다면 표시
                    if failed_stocks:
                        st.warning(f"⚠️ 시뮬레이션 실패 종목 ({len(failed_stocks)}개): {', '.join(sorted(failed_stocks))}")

            else:
                st.write("⚠️ 시뮬레이션 결과가 없습니다.")    

    with tabs[3]:  # 🛠 마이페이지 설정
        setup_my_page()            
    
    with tabs[4]:
        st.header("🏠 자동 트레이딩 봇 잔고")
        
        data = {
            "Trading Bot Name": [],
            "Symbol Name": [],
            "Symbol": [],
            "Avg Price": [],
            "Profit": [],
            "Profit Rate": [],
            "Quantity": [],
            "Market": []
        }

        auto_trading_balance = list(AutoTradingBalance.scan())

        # sorted_result = sorted(
        #     result,
        #     key=lambda x: (x.trading_logic, -x.trade_date, x.symbol_name) #trade_date 최신 순
        # )
        
        # for row in sorted_result:
        #     # 초 단위로 변환
        #     sec_timestamp = row.trade_date / 1000
        #     # 포맷 변환
        #     formatted_trade_date = datetime.fromtimestamp(sec_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        for balance in auto_trading_balance:
            data["Trading Bot Name"].append(balance.trading_bot_name)
            data["Symbol Name"].append(balance.symbol_name)
            data["Symbol"].append(balance.symbol)
            data["Avg Price"].append(balance.avg_price)
            data["Profit"].append(balance.profit)
            data["Profit Rate"].append(balance.profit_rate)
            data["Quantity"].append(balance.quantity)
            data["Market"].append(balance.market)

        df = pd.DataFrame(data)
        
        # AgGrid로 테이블 표시
        AgGrid(
            df,
            editable=True,
            sortable=True,
            filter=True,
            resizable=True,
            theme='streamlit',
            fit_columns_on_grid_load=True,  # 열 너비 자동 조정
            update_mode=GridUpdateMode.NO_UPDATE  # ✅ 핵심! 클릭해도 아무 일 없음
        )

if __name__ == "__main__":
        # Streamlit 실행 시 로그인 여부 확인
        
    # ✅ 현재 쿼리 파라미터로 페이지 상태 확인
    params = st.query_params
    is_logged_in = params.get("login", "false") == "true"
    current_page = params.get("page", "login")
        
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = is_logged_in

    if st.session_state["authenticated"] and current_page == 'main':
        main()
    else:
        login_page()