import sys
import os
import io
import streamlit as st
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder
import pandas as pd
from datetime import datetime, date, timedelta
import pytz
import streamlit.components.v1 as components
from streamlit_lightweight_charts import renderLightweightCharts
import json
import numpy as np
import plotly.express as px
import requests
import time

# 프로젝트 루트를 PYTHONPATH에 추가
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.utils.dynamodb.model.stock_symbol_model import StockSymbol, StockSymbol2
from app.utils.dynamodb.model.trading_history_model import TradingHistory
from app.utils.dynamodb.model.simulation_history_model import SimulationHistory
from app.utils.dynamodb.model.user_info_model import UserInfo
from app.utils.dynamodb.model.auto_trading_balance_model import AutoTradingBalance
from app.utils.utils import setup_env


# env 파일 로드
setup_env()

backend_base_url = os.getenv('BACKEND_BASE_URL')

def draw_lightweight_chart(data_df, selected_indicators):


    # 차트 color
    COLOR_BULL = 'rgba(236, 57, 72, 1)' # #26a69a
    COLOR_BEAR = 'rgba(74, 86, 160, 1)'  # #ef5350

    # Some data wrangling to match required format
    data_df = data_df.reset_index()
    data_df.columns = [col.lower() for col in data_df.columns] #모두 소문자로 수정
    
    data_df['time'] = pd.to_datetime(data_df['time']).dt.strftime('%Y-%m-%d')

    buy_signal_df = data_df[data_df['buy_signal'].notna()]
    sell_signal_df = data_df[data_df['sell_signal'].notna()]

    # export to JSON format
    candles = json.loads(data_df.to_json(orient = "records"))

    bollinger_band_upper = json.loads(data_df.dropna(subset=['upper']).rename(columns={"upper": "value",}).to_json(orient = "records"))
    bollinger_band_middle = json.loads(data_df.dropna(subset=['middle']).rename(columns={"middle": "value",}).to_json(orient = "records"))
    bollinger_band_lower = json.loads(data_df.dropna(subset=['lower']).rename(columns={"lower": "value",}).to_json(orient = "records"))

    ema_89 = json.loads(data_df.dropna(subset=['ema_89']).rename(columns={"ema_89": "value"}).to_json(orient="records"))
    ema_13 = json.loads(data_df.dropna(subset=['ema_13']).rename(columns={"ema_13": "value"}).to_json(orient="records"))
    ema_21 = json.loads(data_df.dropna(subset=['ema_21']).rename(columns={"ema_21": "value"}).to_json(orient="records"))
    ema_55 = json.loads(data_df.dropna(subset=['ema_55']).rename(columns={"ema_55": "value"}).to_json(orient="records"))
    ema_5 = json.loads(data_df.dropna(subset=['ema_5']).rename(columns={"ema_5": "value"}).to_json(orient="records"))
    
    sma_5 = json.loads(data_df.dropna(subset=['sma_5']).rename(columns={"sma_5": "value"}).to_json(orient="records"))
    sma_20 = json.loads(data_df.dropna(subset=['sma_20']).rename(columns={"sma_20": "value"}).to_json(orient="records"))
    sma_40 = json.loads(data_df.dropna(subset=['sma_40']).rename(columns={"sma_40": "value"}).to_json(orient="records"))
    sma_200 = json.loads(data_df.dropna(subset=['sma_200']).rename(columns={"sma_200": "value"}).to_json(orient="records"))
    sma_120 = json.loads(data_df.dropna(subset=['sma_120']).rename(columns={"sma_120": "value"}).to_json(orient="records"))
    
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
        
                # EMA 5
    if "ema_5" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_5,
            "options": {
                "color": 'black', #검은색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })
        
        # EMA 10
    if "ema_13" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_13,
            "options": {
                "color": 'rgba(255, 0, 0, 1)', #빨간색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })
        
                # EMA 20
    if "ema_21" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_21,
            "options": {
                "color": 'rgba(0, 255, 0, 1)',  # 초록색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })

        # EMA 50
    if "ema_55" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_55,
            "options": {
                "color": 'rgba(0, 0, 255, 1)',  # 파란색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": False,
                "priceLineVisible": False,
            },
        })
        
        # EMA 60
    if "ema_89" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": ema_89,
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
    if "sma_200" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": sma_200,
            "options": {
                "color": 'orange', #청록색
                "lineWidth": 1.5,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        })
        
    if "sma_120" in selected_indicators:
        seriesCandlestickChart.append({
            "type": 'Line',
            "data": sma_120,
            "options": {
                "color": 'purple', #청록색
                "lineWidth": 1.5,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        })
        
        # 📌 추세선 파라미터 입력
    lookback_prev = 7
    lookback_next = 7

    # 1. 고점/저점 수평선 추출
    high_lines, low_lines = find_horizontal_lines(data_df, lookback_prev, lookback_next)

    # 2. 중복 제거
    # high_lines = remove_similar_levels(high_lines, threshold=0.01)
    # low_lines = remove_similar_levels(low_lines, threshold=0.01)

    # # 3. 최근 기준으로 필터링
    # recent_dates = set(data_df['time'][-60:])
    # high_lines = [line for line in high_lines if line['time'] in recent_dates]
    # low_lines = [line for line in low_lines if line['time'] in recent_dates]

    # # 4. 상위 N개 선만 남김
    # high_lines = sorted(high_lines, key=lambda x: -x['value'])[:5]
    # low_lines = sorted(low_lines, key=lambda x: x['value'])[:5]

    # 5. 추세선 생성
    high_trendline = create_high_trendline(high_lines)
    low_trendline = create_low_trendline(low_lines)

    # 6. 시리즈에 추가
    if "horizontal_high" in selected_indicators:
        seriesCandlestickChart.extend(create_horizontal_line_segments(high_lines, candles))

    if "horizontal_low" in selected_indicators:
        seriesCandlestickChart.extend(create_horizontal_line_segments(low_lines, candles))
            
                # 조건에 따라 시리즈에 추가
    if "high_trendline" in selected_indicators and high_trendline:
        seriesCandlestickChart.append(high_trendline)

    if "low_trendline" in selected_indicators and low_trendline:
        seriesCandlestickChart.append(low_trendline)
                                    
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

def create_high_trendline(high_levels):
    if len(high_levels) < 2:
        return None
    sorted_levels = sorted(high_levels, key=lambda x: x['time'])
    if len(sorted_levels) < 2:
        return None
    return {
        "type": "Line",
        "data": [{"time": l['time'], "value": l['value']} for l in sorted_levels],
        "options": {
            "color": "rgba(0, 0, 0, 0.8)",  # 검은색
            "lineWidth": 2,
            "lineStyle": 2,
            "priceLineVisible": False,
            "lastValueVisible": False,
        }
    }

def create_low_trendline(low_levels):
    if len(low_levels) < 2:
        return None
    sorted_levels = sorted(low_levels, key=lambda x: x['time'])
    if len(sorted_levels) < 2:
        return None
    return {
        "type": "Line",
        "data": [{"time": l['time'], "value": l['value']} for l in sorted_levels],
        "options": {
            "color": "rgba(0, 0, 0, 0.8)",  # 검은색
            "lineWidth": 2,
            "lineStyle": 2,
            "priceLineVisible": False,
            "lastValueVisible": False,
        }
    }
        
def find_horizontal_lines(df, lookback_prev=5, lookback_next=5):
    """
    전봉/후봉 기준으로 중심봉이 고점/저점인지 판별하여 수평선 후보 반환
    """
    highs = []
    lows = []

    for i in range(lookback_prev, len(df) - lookback_next):
        window = df.iloc[i - lookback_prev : i + lookback_next + 1]
        center = df.iloc[i]

        if center['high'] == window['high'].max():
            highs.append({
                "time": center['time'],
                "value": center['high'],
                "color": "rgba(255, 0, 0, 0.6)",
                "lineWidth": 1,
                "priceLineVisible": False,
                "lastValueVisible": False
            })

        if center['low'] == window['low'].min():
            lows.append({
                "time": center['time'],
                "value": center['low'],
                "color": "rgba(0, 0, 255, 0.6)",
                "lineWidth": 1,
                "priceLineVisible": False,
                "lastValueVisible": False
            })

    return highs, lows


def create_horizontal_line_segments(lines, candles):
    if not candles:
        return []

    times = [c['time'] for c in candles]
    first_time = times[0]
    last_time = times[-1]

    segments = []
    for line in lines:
        segment = {
            "type": "Line",
            "data": [
                {"time": first_time, "value": line["value"]},
                {"time": last_time, "value": line["value"]}
            ],
            "options": {
                "color": line["color"],
                "lineWidth": line["lineWidth"],
                "priceLineVisible": line["priceLineVisible"],
                "lastValueVisible": line["lastValueVisible"],
            }
        }
        segments.append(segment)
    return segments

def remove_similar_levels(levels, threshold=0.01):
    filtered = []
    for level in levels:
        if all(abs(level['value'] - f['value']) / f['value'] > threshold for f in filtered):
            filtered.append(level)
    return filtered


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
            entry['trading_logic'] = '상승추세형2'
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
            entry['trading_logic'] =  '상승추세형3'
        elif entry.get('trading_logic') == 'rsi_trading2':
            entry['trading_logic'] =  'rsi2'
        elif entry.get('trading_logic') == 'ema_crossover_trading':
            entry['trading_logic'] =  '눌림'
        elif entry.get('trading_logic') == 'should_sell':
            entry['trading_logic'] =  '추세 손절'
        elif entry.get('trading_logic') == 'break_prev_low':
            entry['trading_logic'] =  '볼린저밴드 이탈'
        elif entry.get('trading_logic') == 'sell_on_support_break':
            entry['trading_logic'] =  '지지선'
        elif entry.get('trading_logic') == 'anti_retail_ema_entry':
            entry['trading_logic'] =  '반개미'                                                                                                                                                                            
        elif entry.get('trading_logic') == 'trendline_breakout_trading':
            entry['trading_logic'] =  '고점 돌파'
        elif entry.get('trading_logic') == 'should_buy':
            entry['trading_logic'] =  'should_buy'
        elif entry.get('trading_logic') == 'horizontal_low_sell':
            entry['trading_logic'] =  'horizontal_low_sell'                         
        elif entry.get('trading_logic') == 'should_buy_break_high_trend':
            entry['trading_logic'] =  'should_buy_break_high_trend'
                        
def login_page():
    """
    로그인 페이지: 사용자 로그인 및 세션 상태 관리
    """
    st.title("🔑 LOGIN PAGE")

    # 사용자 입력 받기
    username = st.text_input("아이디", key="username")
    password = st.text_input("비밀번호", type="password", key="password")
    
    # 간단한 사용자 검증 (실제 서비스에서는 DB 연동 필요)
    if st.button("LOGIN"):
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
        

def setup_simulation_tab():
    """
    공통적으로 사용할 사이드바 UI를 설정하는 함수
    """
    
    id = 'id1'
    
    current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    # 사용자 입력
    # user_name = st.text_input("User Name", value="홍석문")
    start_date = st.date_input("Start Date", value=date(2023, 1, 1))
    end_date = st.date_input("End Date", value=current_date_kst)
    target_trade_value_krw = st.number_input("Target Trade Value (KRW)", value=1000000, step=100000)

    result = list(StockSymbol.scan(
        filter_condition=((StockSymbol.type == 'kospi200') | (StockSymbol.type == 'kosdaq150') | (StockSymbol.type == 'NASDAQ') | (StockSymbol.type == 'etf') )
    ))
    
    type_order = {
    'kospi200': 1,
    'NASDAQ': 2,
    'kosdaq150': 0,
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
    
    selected_stock = st.selectbox("Select a Stock", list(symbol_options.keys()))
    selected_interval = st.selectbox("Select Chart Interval", list(interval_options.keys()))
    selected_buy_logic = st.multiselect("Select Buy Logic(s):", list(available_buy_logic.keys()))
    selected_sell_logic = st.multiselect("Select Sell Logic(s):", list(available_sell_logic.keys()))
    
    # 3% 매수 조건 체크박스 (체크하면 'Y', 체크 해제하면 'N')
    buy_condition_enabled = st.checkbox("매수 제약 조건 활성화")  # True / False 반환
    buy_condition_yn = "Y" if buy_condition_enabled else "N"
    
    # 사용자가 직접 매수 퍼센트 (%) 입력 (기본값 3%)
    if buy_condition_yn == 'Y':
        buy_percentage = st.number_input("퍼센트 (%) 입력", min_value=0.0, max_value=100.0, value=3.0, step=0.1)
    else:
        buy_percentage = None
        
    symbol = symbol_options[selected_stock]
    interval = interval_options[selected_interval]
    
    selected_buyTrading_logic = [available_buy_logic[logic] for logic in selected_buy_logic] if selected_buy_logic else []
    selected_sellTrading_logic = [available_sell_logic[logic] for logic in selected_sell_logic] if selected_sell_logic else []
    
    #mode
    ohlc_mode_checkbox = st.checkbox("차트 연결 모드")  # True / False 반환
    ohlc_mode = "continuous" if ohlc_mode_checkbox else "default"
    
        # ✅ 실제 투자 조건 체크박스
    real_trading_enabled = st.checkbox("💰 실제 투자자본 설정")
    real_trading_yn = "Y" if real_trading_enabled else "N"

    # ✅ 매수 퍼센트 입력
    initial_capital = None
    if real_trading_yn == "Y":
        initial_capital = st.number_input("💰 초기 투자 자본 (KRW)", min_value=0, value=10000000, step=1000000)
        
    use_take_profit = st.checkbox("익절 조건", value=False)
    take_profit_ratio = st.number_input("익절(%)", value=5.0, min_value=0.0,  key="take_profit_ratio")

    use_stop_loss = st.checkbox("손절 조건", value=False)
    stop_loss_ratio = st.number_input("손절(%)", value=5.0, min_value=0.0,  key="stop_loss_ratio")
        
    #✅ rsi 조건값 입력
    rsi_buy_threshold = st.number_input("📉 RSI 매수 임계값", min_value=0, max_value=100, value=35, step=1)
    rsi_sell_threshold = st.number_input("📈 RSI 매도 임계값", min_value=0, max_value=100, value=70, step=1)
    rsi_period = st.number_input("📈 RSI 기간 설정", min_value=0, max_value=100, value=25, step=1)
    
    # 📌 Streamlit 체크박스 입력
    st.subheader("📊 차트 지표 선택")
    # 체크박스로 사용자 선택 받기
    selected_indicators = []
    if st.checkbox("EMA 5(검)", value=True):
        selected_indicators.append("ema_5")
    if st.checkbox("EMA 13(빨)", value=True):
        selected_indicators.append("ema_13")
    if st.checkbox("EMA 21(초)", value=True):
        selected_indicators.append("ema_21")
    if st.checkbox("EMA 55(파)", value=True):
        selected_indicators.append("ema_55")        
    if st.checkbox("EMA 89(청록)", value=True):
        selected_indicators.append("ema_89")
    if st.checkbox("SMA 5", value=False):
        selected_indicators.append("sma_5")
    if st.checkbox("SMA 20", value=False):
        selected_indicators.append("sma_20")
    if st.checkbox("SMA 40", value=False):
        selected_indicators.append("sma_40")
    if st.checkbox("SMA 200", value=False):
        selected_indicators.append("sma_200")
    if st.checkbox("SMA 120", value=False):
        selected_indicators.append("sma_120")                 
    if st.checkbox("bollinger band", value=False):
        selected_indicators.append("bollinger")
    if st.checkbox("horizontal_high", value=False):
        selected_indicators.append("horizontal_high")
    if st.checkbox("horizontal_low", value=False):
        selected_indicators.append("horizontal_low")
    if st.checkbox("high_trendline", value=False):
        selected_indicators.append("high_trendline")
    if st.checkbox("low_trendline", value=False):
        selected_indicators.append("low_trendline")         
        
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
        "initial_capital" : initial_capital,
        "use_take_profit" : use_take_profit,
        "take_profit_ratio": take_profit_ratio,
        "use_stop_loss": use_stop_loss,
        "stop_loss_ratio": stop_loss_ratio
    }

def read_csv_from_presigned_url(presigned_url):

    print(f"presigned_url = {presigned_url}")
    response = requests.get(presigned_url)
    response.raise_for_status()  # 에러 나면 여기서 멈춤
    csv_buffer = StringIO(response.text)
    df = pd.read_csv(csv_buffer)
    return df

def read_json_from_presigned_url(presigned_url):
    print(f"presigned_url = {presigned_url}")
    
    response = requests.get(presigned_url)
    response.raise_for_status()  # 오류 발생 시 예외 발생
    
    # response.text 또는 response.json() 선택 가능
    # 만약 JSON 파일 구조가 DataFrame으로 바로 변환 가능한 형식이면:
    data = response.json()
    
    return data

def format_date_ymd(value):
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    elif isinstance(value, str):
        return value[:10]  # 'YYYY-MM-DD' 형식만 자름
    else:
        return str(value)  # 혹시 모를 예외 처리

            # ✅ 함수: 가상 익절/손절 판단
def simulate_virtual_sell(df, start_idx, buy_price, take_profit_ratio, stop_loss_ratio):
    for i in range(start_idx + 1, len(df)):
        close = df["Close"].iloc[i]
        roi = ((close - buy_price) / buy_price) * 100

        if roi >= take_profit_ratio:
            return "take_profit", roi, df.index[i]
        elif roi <= -stop_loss_ratio:
            return "stop_loss", roi, df.index[i]
    return None, None, None
            

def draw_bulk_simulation_result(simulation_settings, results, failed_stocks):

    signal_logs = []
    
    if results:
        results_df = pd.DataFrame(results)

        results_df["sim_date"] = pd.to_datetime(results_df["sim_date"])
        results_df = results_df.sort_values(by=["sim_date", "symbol"]).reset_index(drop=True)
        results_df["sim_date"] = results_df["sim_date"].dt.strftime("%Y-%m-%d")

        reorder_columns = [
            "sim_date", "symbol", "initial_capital", "portfolio_value", "buy_count", "sell_count", "quantity",
            "realized_pnl", "realized_roi", "unrealized_pnl", "unrealized_roi",
            "total_quantity", "average_price", "take_profit_hit", "stop_loss_hit", "fee_buy", "fee_sell", "tax", "total_costs", 'buy_logic_count', "signal_reasons", "total_buy_cost", "buy_signal_info", "ohlc_data_full", "history"
        ]
        results_df = results_df[[col for col in reorder_columns if col in results_df.columns]]

        for col in ["realized_roi", "unrealized_roi"]:
            if col in results_df.columns:
                results_df[col] = results_df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)
        
        # st.subheader("📋 시뮬레이션 결과 테이블")
        # st.dataframe(results_df, use_container_width=True)

        signal_logs = []
        for row in results:
            raw_reasons = row.get("signal_reasons", [])
            
            # 문자열이면 리스트로 변환
            if isinstance(raw_reasons, str):
                reasons_list = [raw_reasons]
            # 리스트인데 내부에 리스트가 있으면 flatten
            elif isinstance(raw_reasons, list):
                if raw_reasons and isinstance(raw_reasons[0], list):
                    reasons_list = [item for sublist in raw_reasons for item in sublist]
                else:
                    reasons_list = raw_reasons
            else:
                reasons_list = []

            reasons = ", ".join(map(str, reasons_list))

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

        # ✅ 시뮬레이션 params
        st.markdown("---")
        st.subheader("📊 시뮬레이션 설정")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("시작 날짜", format_date_ymd(simulation_settings["start_date"]))
            st.metric("종료 날짜", format_date_ymd(simulation_settings["end_date"]))
            st.metric("일자 별", simulation_settings.get("interval") if simulation_settings.get("interval") else "없음")
            st.metric("매수 제약 조건", simulation_settings["buy_condition_yn"] if simulation_settings.get("buy_condition_yn") else "없음")
        with col2:
            st.metric("초기 자본", f"{int(simulation_settings['initial_capital']):,}" if simulation_settings.get("initial_capital") else "없음")
            st.metric("자본 비율", simulation_settings["target_trade_value_ratio"] if simulation_settings.get("target_trade_value_ratio") else "없음")
            st.metric("목표 거래 금액", simulation_settings.get("target_trade_value_krw") if simulation_settings.get("target_trade_value_krw") else "없음")
            st.metric("매수 제약 조건 비율", simulation_settings["buy_percentage"] if simulation_settings.get("buy_percentage") else "없음")
        with col3:
            st.metric("rsi_period", simulation_settings["rsi_period"] if simulation_settings.get("rsi_period") else "없음")
            st.metric("rsi_buy_threshold", simulation_settings["rsi_buy_threshold"] if simulation_settings.get("rsi_buy_threshold") else "없음")
            st.metric("rsi_sell_threshold", simulation_settings["rsi_sell_threshold"] if simulation_settings.get("rsi_sell_threshold") else "없음")
        with col4:
            st.metric("익절 여부", simulation_settings["use_take_profit"] if simulation_settings.get("use_take_profit") else "없음")
            st.metric("익절 비율", simulation_settings["take_profit_ratio"] if simulation_settings.get("use_take_profit") else "없음")
            st.metric("손절 여부", simulation_settings["use_stop_loss"] if simulation_settings.get("use_stop_loss") else "없음")
            st.metric("손절 비율", simulation_settings["stop_loss_ratio"] if simulation_settings.get("use_stop_loss") else "없음")

        # 한글 로직 이름 맵핑
        file_path = "./dashboard_web/trading_logic.json"
        with open(file_path, "r", encoding="utf-8") as f:
            trading_logic = json.load(f)

        buy_trading_logic = simulation_settings["buy_trading_logic"]
        sell_trading_logic = simulation_settings["sell_trading_logic"]

        # 코드 기준으로 필요한 항목만 필터링
        filtered_buy_logic = {
            k: v for k, v in trading_logic["available_buy_logic"].items() if v in buy_trading_logic
        }
        filtered_sell_logic = {
            k: v for k, v in trading_logic["available_sell_logic"].items() if v in sell_trading_logic
        }

        # 최종 결과
        trading_logic_dict = {
            "buy_trading_logic": filtered_buy_logic,
            "sell_trading_logic": filtered_sell_logic
        }

        st.write("###### 선택한 종목")
        st.json(simulation_settings["selected_symbols"], expanded=False)
        st.write("###### 매수 로직")
        st.json(trading_logic_dict["buy_trading_logic"], expanded=False)
        st.write("###### 매도 로직")
        st.json(trading_logic_dict["sell_trading_logic"], expanded=False)
        st.markdown("---")

        if signal_logs:
            df_signals = pd.DataFrame(signal_logs)
            df_signals["sim_date"] = pd.to_datetime(df_signals["sim_date"])
            df_signals = df_signals.sort_values(by=["sim_date", "symbol"]).reset_index(drop=True)
            df_signals["sim_date"] = df_signals["sim_date"].dt.strftime("%Y-%m-%d")

            st.subheader("📌 매매 신호가 발생한 날짜 (거래 여부와 무관)")
            st.dataframe(df_signals, use_container_width=True)

        # ✅ 실제 거래 발생 테이블 (추가)
        df_trades = results_df[
            (results_df["buy_count"] > 0) | (results_df["sell_count"] > 0)
        ].copy()

        if not df_trades.empty:
            df_trades["trade_pnl"] = df_trades["realized_pnl"].apply(
                lambda x: f"{x:,.0f} KRW" if pd.notnull(x) and x != 0 else "-"
            )

            df_trades["total_costs"] = df_trades["total_costs"].apply(
                    lambda x: f"{x:,.0f} KRW" if pd.notnull(x) and x != 0 else "-"
                )

            df_trades["fee_buy"] = df_trades["fee_buy"].apply(lambda x: f"{x:,.0f} KRW" if x > 0 else "-")
            df_trades["fee_sell"] = df_trades["fee_sell"].apply(lambda x: f"{x:,.0f} KRW" if x > 0 else "-")
            df_trades["tax"] = df_trades["tax"].apply(lambda x: f"{x:,.0f} KRW" if x > 0 else "-")

            # 익절/손절 텍스트
            if "take_profit_hit" in df_trades.columns:
                df_trades["take_profit_hit"] = df_trades["take_profit_hit"].apply(
                    lambda x: "✅ 익절" if x else ""
                )
            if "stop_loss_hit" in df_trades.columns:
                df_trades["stop_loss_hit"] = df_trades["stop_loss_hit"].apply(
                    lambda x: "⚠️ 손절" if x else ""
                )

            # ✅ 사유 컬럼 만들기 (존재할 때만 처리)
            if "signal_reasons" in df_trades.columns:
                def format_reasons(x):
                    if isinstance(x, str):
                        return x
                    elif isinstance(x, list):
                        if x and isinstance(x[0], list):
                            # flatten 후 문자열 join
                            flat = [item for sublist in x for item in sublist]
                            return ", ".join(map(str, flat))
                        else:
                            return ", ".join(map(str, x))
                    else:
                        return ""

                df_trades["reason"] = df_trades["signal_reasons"].apply(format_reasons)
            else:
                df_trades["reason"] = "-"

            # for i, row in df_trades.iterrows():
            #     history = row.get("history", [])
            #     sim_date = row["sim_date_dt"].date()
                
            columns_to_show = [
                "sim_date", "symbol", "buy_count", "sell_count", "quantity",
                "trade_pnl", 'fee_buy', "fee_sell", "tax", "total_costs", "reason"
            ]

            # ✅ 컬럼이 존재할 경우에만 추가
            if "take_profit_hit" in df_trades.columns:
                columns_to_show.append("take_profit_hit")
            if "stop_loss_hit" in df_trades.columns:
                columns_to_show.append("stop_loss_hit")
                    
            st.subheader("📅 실제 거래 발생 요약 (날짜별)")
            st.dataframe(df_trades[columns_to_show], use_container_width=True)

        if not df_trades.empty and "reason" in df_trades.columns and "realized_pnl" in df_trades.columns:
            # 문자열 기준 첫 번째 이유 추출
            df_trades["sell_logic_name"] = df_trades["reason"].apply(
                lambda x: x.split(",")[0].strip() if isinstance(x, str) and x else "기타"
            )

            df_sell_summary = df_trades[df_trades["sell_count"] > 0].copy()

            logic_summary = df_sell_summary.groupby("sell_logic_name").agg(
                거래수=("sell_count", "sum"),
                총실현손익=("realized_pnl", "sum"),
                평균손익=("realized_pnl", "mean")
            ).fillna(0).reset_index()

            logic_summary["총실현손익"] = logic_summary["총실현손익"].apply(lambda x: f"{x:,.0f} KRW")
            logic_summary["평균손익"] = logic_summary["평균손익"].apply(lambda x: f"{x:,.0f} KRW")

            st.markdown("---")
            st.subheader("📉 매도 로직별 실현손익 요약")
            st.dataframe(logic_summary, use_container_width=True)
            
        # ✅ 요약 통계
        if not results_df.empty:
            df_last_unrealized = results_df.sort_values("sim_date").groupby("symbol").last()

            total_realized_pnl = results_df["realized_pnl"].sum()
            total_unrealized_pnl = df_last_unrealized["unrealized_pnl"].sum()

            initial_capital = simulation_settings["initial_capital"]
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
            with col2:
                st.metric("📊 초기 자본 대비 평균 실현 손익률", f"{avg_realized_roi_per_capital:.2f}%" if avg_realized_roi_per_capital is not None else "N/A")
                st.metric("📉 초기 자본 대비 평균 총 손익률", f"{avg_total_roi_per_capital:.2f}%" if avg_total_roi_per_capital is not None else "N/A")

            # ✅ 세부 통계 추가
            total_buy_count = results_df["buy_count"].sum()
            total_sell_count = results_df["sell_count"].sum()
            total_take_profit = results_df["take_profit_hit"].sum() if "take_profit_hit" in results_df.columns else 0
            total_stop_loss = results_df["stop_loss_hit"].sum() if "stop_loss_hit" in results_df.columns else 0

            tp_pnl = results_df[results_df["take_profit_hit"] == True]["realized_pnl"].sum() if "take_profit_hit" in results_df.columns else 0
            sl_pnl = results_df[results_df["stop_loss_hit"] == True]["realized_pnl"].sum() if "stop_loss_hit" in results_df.columns else 0
            logic_sell_pnl = results_df[
                (results_df["sell_count"] > 0) &
                (~results_df.get("take_profit_hit", False)) &
                (~results_df.get("stop_loss_hit", False))
            ]["realized_pnl"].sum()
            
            total_fee_buy = results_df["fee_buy"].sum()
            total_fee_sell = results_df["fee_sell"].sum()
            total_tax = results_df["tax"].sum()
            total_costs = results_df["total_costs"].sum()
            total_buy_logic_count = results_df['buy_logic_count'].sum()
            roi_per_total_buy_cost = ((total_realized_pnl + total_unrealized_pnl) / results_df['total_buy_cost'].sum()) * 100
            total_take_profit_per_total_sell_count = (total_take_profit / total_sell_count) * 100
            st.markdown("---")
            st.subheader("📊 추가 세부 요약 통계")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("🔄 총 매수로직 횟수", f"{total_buy_logic_count}")
                st.metric("🟢 총 매수 횟수", f"{total_buy_count}")
                st.metric("🔴 총 매도 횟수", f"{total_sell_count}")
                st.metric("✅ 익절 횟수", f"{total_take_profit}")
                st.metric("⚠️ 손절 횟수", f"{total_stop_loss}")

            with col2:
                st.metric("💸 익절로 인한 손익", f"{tp_pnl:,.0f} KRW")
                st.metric("💥 손절로 인한 손익", f"{sl_pnl:,.0f} KRW")
                st.metric("🔄 로직 매도로 인한 손익", f"{logic_sell_pnl:,.0f} KRW")
                st.metric("🔄 총 매수 금액 대비 수익률", f"{roi_per_total_buy_cost:.2f}%")
                st.metric("💸 매도 횟수 대비 익절률", f"{total_take_profit_per_total_sell_count:.2f}%")
            col3, col4 = st.columns(2)
            with col3:
                st.metric("🧾 총 매수 수수료", f"{total_fee_buy:,.0f} KRW")
                st.metric("🧾 총 매도 수수료", f"{total_fee_sell:,.0f} KRW")
                st.metric("📜 총 거래세", f"{total_tax:,.0f} KRW")
            with col4:
                st.metric("💰 총 수수료 비용 합계", f"{total_costs:,.0f} KRW")

            # ✅ 거래 여부와 무관한 신호 발생 통계 요약
            if signal_logs:
                df_signals_stat = pd.DataFrame(signal_logs)
                total_buy_signals = len(df_signals_stat[df_signals_stat["signal"] == "BUY_SIGNAL"])
                total_sell_signals = len(df_signals_stat[df_signals_stat["signal"] == "SELL_SIGNAL"])

                # 익절/손절은 거래가 발생했을 때만 측정 가능 → 거래 결과로부터
                total_tp_from_trades = results_df["take_profit_hit"].sum() if "take_profit_hit" in results_df.columns else 0
                total_sl_from_trades = results_df["stop_loss_hit"].sum() if "stop_loss_hit" in results_df.columns else 0

                take_profit_ratio_per_sell_signal = (
                    (total_tp_from_trades / total_sell_signals) * 100 if total_sell_signals > 0 else None
                )

                st.markdown("---")
                st.subheader("📌 매매 신호 통계 요약 (거래 여부 무관)")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📍 총 매수 신호", total_buy_signals)
                    st.metric("📍 총 매도 신호", total_sell_signals)
                with col2:
                    st.metric("✅ 익절 발생 (총)", total_tp_from_trades)
                    st.metric("⚠️ 손절 발생 (총)", total_sl_from_trades)
                    st.metric("📈 매도 신호 대비 익절률", f"{take_profit_ratio_per_sell_signal:.2f}%" if take_profit_ratio_per_sell_signal is not None else "N/A")
                    

            # st.markdown("---")
            # st.subheader("🛠️ 가상 익절/손절 판단 디버깅")

            # debug_rows = 0
            # for row in results:
            #     signal_info = row.get("buy_signal_info")
            #     df_full = row.get("ohlc_data_full")

            #     if signal_info:
            #         st.write(
            #         f"📘 BUY_SIGNAL 발생: {row['symbol']} on {signal_info['date'].strftime('%Y-%m-%d')} @ {signal_info['price']}"
            #     )
            #     else:
            #         st.write(f"🚫 No buy_signal_info for {row['symbol']}")
            #         continue

            #     if df_full is None:
            #         st.write(f"❌ {row['symbol']} → ohlc_data_full 없음")
            #         continue
            #     st.write(f"📂 df_full type: {type(df_full)}")
            #     st.write(f"🧩 df_full.index: {df_full.index if hasattr(df_full, 'index') else '❌ index 없음'}")

            #     try:
            #         start_idx = df_full.index.get_loc(pd.Timestamp(signal_info["date"]))
            #     except KeyError:
            #         st.write(f"❌ {row['symbol']} → Index에서 {signal_info['date']} 못 찾음")
            #         continue

            #     outcome, roi, outcome_date = simulate_virtual_sell(
            #         df_full, start_idx, signal_info["price"],
            #         take_profit_ratio=simulation_settings["take_profit_ratio"],
            #         stop_loss_ratio=simulation_settings["stop_loss_ratio"]
            #     )

                # debug_rows += 1
                # if debug_rows >= 5:
                #     break  # 디버깅 출력 너무 많으면 중단
    
                # ✅ 거래 여부 무관, 신호 발생 기준 가상 익절/손절 내역 추적
                # virtual_hits = []

                # for row in results:
                #     signal_info = row.get("buy_signal_info")
                #     df_full = row.get("ohlc_data_full")

                #     if signal_info is None:
                #         st.write(f"🚫 No buy_signal_info for {row['symbol']}")
                #         continue
                #     if df_full is None or not isinstance(df_full, pd.DataFrame):
                #         st.write(f"❌ ohlc_data_full이 잘못되었거나 없음: {row['symbol']}")
                #         continue

                #     # ✅ 안전하게 날짜 변환
                #     try:
                #         signal_dt = pd.to_datetime(signal_info["date"]).normalize()
                #     except Exception as e:
                #         st.write(f"❌ 날짜 변환 실패: {e}")
                #         continue

                #     try:
                #         df_full.index = pd.to_datetime(df_full.index).normalize()
                #         start_idx = df_full.index.get_loc(signal_dt)
                #     except KeyError:
                #         st.write(f"❌ {row['symbol']} → df_full.index에 {signal_dt} 없음")
                #         continue
                #     except Exception as e:
                #         st.write(f"❌ index 오류: {e}")
                #         continue

                #     outcome, roi, outcome_date = simulate_virtual_sell(
                #         df_full, start_idx, signal_info["price"],
                #         take_profit_ratio=simulation_settings["take_profit_ratio"],
                #         stop_loss_ratio=simulation_settings["stop_loss_ratio"]
                #     )

                #     if outcome:
                #         virtual_hits.append({
                #             "symbol": row["symbol"],
                #             "buy_date": signal_dt.strftime("%Y-%m-%d"),
                #             "outcome_date": outcome_date.strftime("%Y-%m-%d"),
                #             "type": "✅ 익절" if outcome == "take_profit" else "⚠️ 손절",
                #             "roi": f"{roi:.2f}%",
                #             "reason": "가상 매수 후 조건 충족"
                #         })

                # if virtual_hits:
                #     df_virtual = pd.DataFrame(virtual_hits)
                #     st.markdown("---")
                #     st.subheader("🧪 거래 여부 무관: 가상 매수 기준 익절/손절 내역")
                #     st.dataframe(df_virtual, use_container_width=True)
                # else:
                #     st.info("📭 가상 익절/손절 내역 없음")
                                    
        if failed_stocks:
            st.warning(f"⚠️ 시뮬레이션 실패 종목 ({len(failed_stocks)}개): {', '.join(sorted(failed_stocks))}")

    else:
        st.warning("⚠️ 시뮬레이션 결과가 없습니다.")

def main():
    
    st.set_page_config(layout="wide")
    col1, col2, col3 = st.columns([6, 1, 1])

    with col3:
        if st.button("LOGOUT"):
            st.session_state["authenticated"] = False
            st.query_params = {"page" : "login", "login": "false"}
            st.rerun()  # 로그아웃 후 페이지 새로고침
            
    st.title("FSTS SIMULATION")
    # 상단에 3등분 컬럼 만들기
    # col1, col2, col3 = st.columns([6, 1, 1])

    # with col3:
    #     if st.button("LOGOUT"):
    #         st.session_state["authenticated"] = False
    #         st.query_params = {"page" : "login", "login": "false"}
    #         st.rerun()  # 로그아웃 후 페이지 새로고침
    
    # 탭 생성
    tabs = st.tabs(["🏠 Bot Transaction History", "📈 Simulation Graph", "📊 KOSPI200 Simulation", "📊 Simulation Result", "📈Auto Trading Bot Balance", "🏆Ranking"])

    # 각 탭의 내용 구성
    with tabs[0]:
        st.header("🏠  Bot Transaction History")
        
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
    
    with tabs[1]:
        st.header("📈 종목 시뮬레이션")

        sidebar_settings = setup_simulation_tab()
        
        if st.button("개별 종목 시뮬레이션 실행", key = 'simulation_button'):
            
            with st.container():
                st.write(f"📊 {sidebar_settings['selected_stock']} 시뮬레이션 실행 중...")
                
                url = f"{backend_base_url}/stock/simulate/single"

                print(f'url = {url}')

                payload = {
                    "user_id": sidebar_settings["id"],
                    "symbol": sidebar_settings["symbol"],
                    "start_date": sidebar_settings["start_date"].isoformat(),
                    "end_date": sidebar_settings["end_date"].isoformat(),
                    "target_trade_value_krw": sidebar_settings["target_trade_value_krw"],
                    "buy_trading_logic": sidebar_settings["buy_trading_logic"],
                    "sell_trading_logic": sidebar_settings["sell_trading_logic"],
                    "interval": sidebar_settings["interval"],
                    "buy_percentage": sidebar_settings["buy_percentage"],
                    "ohlc_mode": sidebar_settings["ohlc_mode"],
                    "rsi_buy_threshold": sidebar_settings["rsi_buy_threshold"],
                    "rsi_sell_threshold": sidebar_settings["rsi_sell_threshold"],
                    "rsi_period": sidebar_settings["rsi_period"],
                    "initial_capital": sidebar_settings["initial_capital"],
                    "use_take_profit": sidebar_settings["use_take_profit"],
                    "take_profit_ratio": sidebar_settings["take_profit_ratio"],
                    "use_stop_loss": sidebar_settings["use_stop_loss"],
                    "stop_loss_ratio": sidebar_settings["stop_loss_ratio"]
                }

                response = requests.post(url, json=payload).json()
                print(response)

                json_url = response['json_url']
                json_data = read_json_from_presigned_url(json_url)
                data_url = json_data['data_url']
                data_df = read_csv_from_presigned_url(data_url)
                trading_history = json_data['trading_history']
                trade_reasons = json_data['trade_reasons']

                # ✅ 상태 저장
                st.session_state["simulation_result"] = {
                    "data_df": data_df,
                    "trading_history": trading_history,
                    "trade_reasons": trade_reasons,
                    "selected_indicators": sidebar_settings['selected_indicators'],
                    "selected_stock": sidebar_settings["selected_stock"]
                }

        # ✅ 이전 시뮬 결과가 있는 경우 표시
        if "simulation_result" in st.session_state:
            result = st.session_state["simulation_result"]
            data_df = result["data_df"]
            trading_history = result["trading_history"]
            trade_reasons = result["trade_reasons"]
            selected_indicators = result["selected_indicators"]

            # CSV 다운로드 버튼
            st.subheader("📥 데이터 다운로드")
            csv_buffer = io.StringIO()
            pd.DataFrame(trade_reasons).to_csv(csv_buffer, index=False)
            st.download_button(
                label="📄 CSV 파일 다운로드",
                data=csv_buffer.getvalue(),
                file_name="trade_reasons.csv",
                mime="text/csv"
            )
            #     simulation_result = {
            #         "data_df": data_df,
            #         "trading_history": trading_history,
            #         "trade_reasons": trade_reasons
            #     }
    
            # result = simulation_result
            # data_df = result["data_df"]
            # trading_history = result["trading_history"]
            # trade_reasons = result["trade_reasons"]
            
            # # CSV 다운로드 버튼 - trade_reasons DataFrame 생성 후 다운로드
            # if trade_reasons:
            #     df_trade = pd.DataFrame(trade_reasons)
            # else:
            #     st.warning("🚨 거래 내역이 없습니다.")
            #     df_trade = pd.DataFrame()
            
            # st.subheader("📥 데이터 다운로드")
            # csv_buffer = io.StringIO()
            # df_trade.to_csv(csv_buffer, index=False)
            # st.download_button(
            #     label="📄 CSV 파일 다운로드",
            #     data=csv_buffer.getvalue(),
            #     file_name="trade_reasons.csv",
            #     mime="text/csv"
            # )
            
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
                    
                                        # ✅ 실현 수익률 퍼센트 표시
                    if "realized_roi" in trade_history_df.columns:
                        trade_history_df["realized_roi (%)"] = trade_history_df["realized_roi"].apply(
                            lambda x: f"{x * 100:.2f}%" if pd.notnull(x) else None
                        )
                    
                    st.subheader("📋 Detailed Trade History")
                    st.dataframe(trade_history_df, use_container_width=True)
                else:
                    st.write("No detailed trade history found.")
        else:
            st.info("먼저 시뮬레이션을 실행해주세요.")
            
    with tabs[2]:
        
        id = "id1"  # 사용자 이름 (고정값)
        
        current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()

        start_date = st.date_input("📅 Start Date", value=date(2023, 1, 1))
        end_date = st.date_input("📅 End Date", value=current_date_kst)
        
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
            target_trade_value_ratio = st.slider("💡 초기 자본 대비 매수 비율 (%)", 1, 100, 50) #마우스 커서로 왔다갔다 하는 기능
            target_trade_value_krw = None  # 실제 시뮬 루프에서 매일 계산
        # ✅ 실제 투자 조건 체크박스
        real_trading_enabled = st.checkbox("💰 실제 투자자본 설정", value=True, key="real_trading_enabled")
        real_trading_yn = "Y" if real_trading_enabled else "N"

        # ✅ 매수 퍼센트 입력
        initial_capital = None
        if real_trading_yn == "Y":
            initial_capital = st.number_input("💰 초기 투자 자본 (KRW)", min_value=0, value=10_000_000, step=1_000_000, key="initial_capital")
            
        # ✅ DB에서 종목 리스트 가져오기
        result = list(StockSymbol.scan(
            filter_condition=((StockSymbol.type == 'kospi200') | (StockSymbol.type == 'kosdaq150'))
        ))

        # ✅ StockSymbol2에서도 종목 가져오기 (kosdaq 전체)
        kosdaq_all_result = list(StockSymbol2.scan(
            filter_condition=(StockSymbol2.type == 'kosdaq')
        ))

        type_order = {
            'kospi200': 1,
            'kosdaq150': 2
        }

        # ✅ 정렬
        sorted_items = sorted(
            result,
            key=lambda x: (
                type_order.get(getattr(x, 'type', ''), 99),
                getattr(x, 'symbol_name', '')
            )
        )

        # ✅ 분리
        kospi200_items = [row for row in sorted_items if getattr(row, 'type', '') == 'kospi200']
        kosdaq150_items = [row for row in sorted_items if getattr(row, 'type', '') == 'kosdaq150']
        kosdaq_items = [row for row in kosdaq_all_result if getattr(row, 'type', '') == 'kosdaq']

        kospi200_names = [row.symbol_name for row in kospi200_items]
        kosdaq150_names = [row.symbol_name for row in kosdaq150_items]
        kosdaq_all_names = [row.symbol_name for row in kosdaq_items]

        # ✅ 전체 종목 이름 리스트 (StockSymbol + StockSymbol2)
        all_symbol_names = list(set(
            row.symbol_name for row in (sorted_items + kosdaq_items)
        ))

        # ✅ 병합된 symbol_options
        symbol_options_main = {row.symbol_name: row.symbol for row in sorted_items}
        symbol_options_kosdaq = {row.symbol_name: row.symbol for row in kosdaq_items}
        symbol_options = {**symbol_options_main, **symbol_options_kosdaq}

        # ✅ 버튼 UI
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 4])

        with col1:
            if st.button("✅ 전체 선택"):
                st.session_state["selected_stocks"] = all_symbol_names
                print(len(all_symbol_names))

        with col2:
            if st.button("🏦 코스피 200 선택"):
                st.session_state["selected_stocks"] = kospi200_names
                print(len(kospi200_names))

        with col3:
            if st.button("📈 코스닥 150 선택"):
                st.session_state["selected_stocks"] = kosdaq150_names
                print(len(kosdaq150_names))

        with col4:
            if st.button("📊 코스닥 전체 선택"):
                st.session_state["selected_stocks"] = kosdaq_all_names
                print(len(kosdaq_all_names))

        with col5:
            if st.button("❌ 선택 해제"):
                st.session_state["selected_stocks"] = []

        # ✅ 세션 상태에 저장된 값 중, 현재 옵션에 존재하는 것만 유지
        if "selected_stocks" in st.session_state:
            st.session_state["selected_stocks"] = [
                s for s in st.session_state["selected_stocks"] if s in symbol_options
            ]
            
        # ✅ 사용자가 원하는 종목 선택 (다중 선택 가능)
        selected_stocks = st.multiselect("📌 원하는 종목 선택", all_symbol_names, key="selected_stocks")
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
        buy_condition_yn = st.checkbox("💰 매수 제약 조건 활성화", key="buy_condition_enabled")

        buy_percentage = None
        # ✅ 매수 퍼센트 입력
        if buy_condition_yn:
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

        # 시뮬레이션 polling request 여부 확인
        polling_request = False

        if st.button("✅ 시뮬레이션 전체 실행"):
            
            # 설정 저장
            st.session_state["my_page_settings"] = {
                "id": id,
                "start_date": start_date,
                "end_date": end_date,
                "target_trade_value_krw": target_trade_value_krw,
                "target_trade_value_ratio": target_trade_value_ratio,
                "selected_stocks": selected_stocks, #이름만
                "selected_symbols": selected_symbols, #이름+코드(key,value)
                "interval": interval,
                "buy_trading_logic": selected_buyTrading_logic,
                "sell_trading_logic": selected_sellTrading_logic,
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

            # ✅ 저장된 설정 확인
            if "my_page_settings" in st.session_state:
                st.subheader("📌 저장된 설정값")
                st.json(st.session_state["my_page_settings"], expanded=False)

            with st.spinner("📈 전체 종목 OHLC 및 지표 계산 중..."):
                
                simulation_settings = st.session_state["my_page_settings"]

                url = f"{backend_base_url}/stock/simulate/bulk"

                payload = {
                    "user_id": simulation_settings['id'],
                    "start_date": simulation_settings['start_date'].isoformat(),
                    "end_date": simulation_settings['end_date'].isoformat(),
                    "target_trade_value_krw": simulation_settings['target_trade_value_krw'],
                    "target_trade_value_ratio": simulation_settings['target_trade_value_ratio'],
                    "selected_stocks": simulation_settings['selected_stocks'],
                    "selected_symbols": simulation_settings['selected_symbols'],
                    "interval": simulation_settings['interval'],
                    "buy_trading_logic": simulation_settings['buy_trading_logic'],
                    "sell_trading_logic": simulation_settings['sell_trading_logic'],
                    "buy_condition_yn": simulation_settings['buy_condition_yn'],
                    "buy_percentage": simulation_settings['buy_percentage'],
                    "initial_capital": simulation_settings['initial_capital'],
                    "rsi_buy_threshold": simulation_settings['rsi_buy_threshold'],
                    "rsi_sell_threshold": simulation_settings['rsi_sell_threshold'],
                    "rsi_period": simulation_settings['rsi_period'],
                    "use_take_profit": simulation_settings['use_take_profit'],
                    "take_profit_ratio": simulation_settings['take_profit_ratio'],
                    "use_stop_loss": simulation_settings['use_stop_loss'],
                    "stop_loss_ratio": simulation_settings['stop_loss_ratio']
                }

                response = requests.post(url, json=payload).json()
                simulation_id = None
                simulation_id = response['simulation_id']

                if simulation_id is not None:
                    st.success(f"시뮬레이션 요청 성공! simulation id : {simulation_id}")
                else:
                    st.warning("⚠️ 시뮬레이션 요청에 실패했습니다.")
                get_simulation_result_url = f"{backend_base_url}/stock/simulate/bulk/result"
                result_presigned_url = None

                # 프로그레스 바 초기화
                progress_bar = st.progress(0)
                progress_text = st.empty()  # 숫자 출력을 위한 공간
                
                # polling 으로 현재 상태 확인
                while True:
                    params={"simulation_id": simulation_id}
                    response = requests.get(get_simulation_result_url, params=params).json()
                    print(response)

                    total_task_cnt = response["total_task_cnt"]
                    completed_task_cnt = response["completed_task_cnt"]

                    if total_task_cnt == 0:
                        total_task_cnt = 10000 # 임시

                    progress_bar.progress(completed_task_cnt / total_task_cnt)
                    progress_text.text(f"{completed_task_cnt} / {total_task_cnt} 완료")

                    if response["status"] == "completed":
                        result_presigned_url = response["result_presigned_url"]
                        break

                    time.sleep(5)

                st.success("모든 작업 완료!")
                
                json_data = read_json_from_presigned_url(result_presigned_url)

                results = json_data['results']
                failed_stocks = json_data['failed_stocks']

                draw_bulk_simulation_result(simulation_settings, results, failed_stocks)
    
    with tabs[3]:
        st.header("🏠 Simulation Result")

        data = {
            "simulation_id": [],
            "created_at_dt": [],
            "completed_task_cnt": [],
            "total_task_cnt": [],
            "trigger_type": [],
            "status": [],
            "description": []
        }

        result = list(SimulationHistory.scan())

        sorted_result = sorted(
            result,
            key=lambda x: (-x.created_at) #trade_date 최신 순
        )
        
        for row in sorted_result:
            data["simulation_id"].append(row.simulation_id)
            data["created_at_dt"].append(row.created_at_dt)
            data["completed_task_cnt"].append(row.completed_task_cnt)
            data["total_task_cnt"].append(row.total_task_cnt)
            data["trigger_type"].append(row.trigger_type)
            data["status"].append(row.status)
            data["description"].append(row.description)

        df = pd.DataFrame(data)
        
        # Grid 설정
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('single')  # ✅ 한 행만 선택
        grid_options = gb.build()

        selected_rows = None
        selected_grid_row = None

        # AgGrid로 테이블 표시
        grid_response = AgGrid(
            df,
            key='bulk_simulation_result',
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            sortable=True,  # 정렬 가능
            filter=True,    # 필터링 가능
            resizable=True, # 크기 조절 가능
            theme='streamlit',   # 테마 변경 가능 ('light', 'dark', 'blue', 등)
            fit_columns_on_grid_load=True  # 열 너비 자동 조정
        )

        selected_rows = grid_response["selected_rows"]

        if selected_rows is not None:
            selected_grid_row = grid_response["selected_rows"].iloc[0]
            simulation_id = selected_grid_row["simulation_id"]

            get_simulation_result_url = f"{backend_base_url}/stock/simulate/bulk/result"
            result_presigned_url = None

            params={"simulation_id": simulation_id}
            response = requests.get(get_simulation_result_url, params=params).json()

            if response["status"] == "completed":
                params_presigned_url = response["params_presigned_url"]
                result_presigned_url = response["result_presigned_url"]

                simulation_settings = read_json_from_presigned_url(params_presigned_url)
                result_json_data = read_json_from_presigned_url(result_presigned_url)

                results = result_json_data['results']
                failed_stocks = result_json_data['failed_stocks']
                                
                draw_bulk_simulation_result(simulation_settings, results, failed_stocks)
            
    with tabs[4]:
        st.header("🏠 Auto Trading Bot Balance")
        
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
        
    with tabs[5]:
        
        st.header("Ranking")
        # CSV 파일 로드
        csv_file = "profits_history.csv"
        df = pd.read_csv(csv_file)
        df["date"] = pd.to_datetime(df["date"])

        # 봇 이름 목록 가져오기
        bot_names = df["bot_name"].unique().tolist()
        selected_bots = st.multiselect("🤖 봇 선택", bot_names, default=bot_names)

        # 수익률 종류 선택
        roi_option = st.radio(
            "📈 수익률 종류 선택",
            ("realized_roi", "unrealized_roi", "total_roi"),
            index=2,
            format_func=lambda x: {
                "realized_roi": "실현 수익률",
                "unrealized_roi": "미실현 수익률",
                "total_roi": "총 수익률"
            }[x]
        )

        # 오늘 날짜 기준 데이터만 추출
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_df = df[df["date"] == today_str]
        today_df = today_df[today_df["bot_name"].isin(selected_bots)]

        # 등수 계산 (수익률 높은 순)
        if not today_df.empty:
            today_df = today_df.copy()
            today_df["rank"] = today_df[roi_option].rank(ascending=False, method='min').astype(int)
            today_df = today_df.sort_values("rank")

            st.subheader("🏆 오늘 수익률 순위")
            st.dataframe(today_df[["bot_name", roi_option, "rank"]].rename(columns={
                "bot_name": "Bot 이름",
                roi_option: "수익률 (%)",
                "rank": "등수"
            }), use_container_width=True)
        else:
            st.warning("오늘 날짜 기준 데이터가 없습니다.")

        # 선택된 봇 기준 전체 기간 시계열 그래프
        filtered_df = df[df["bot_name"].isin(selected_bots)]

        fig = px.line(
            filtered_df,
            x="date",
            y=roi_option,
            color="bot_name",
            markers=True,
            title=f"📊 날짜별 {roi_option.replace('_roi', '').capitalize()} 수익률 변화",
            labels={roi_option: "ROI (%)", "date": "날짜"}
        )

        st.plotly_chart(fig, use_container_width=True)


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