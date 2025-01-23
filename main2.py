import streamlit as st
from datetime import date
from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.crud_sql import SQLExecutor
import pandas as pd
from app.utils.database import get_db, get_db_session
import matplotlib.pyplot as plt
from io import BytesIO
import json

sql_executor = SQLExecutor()
# Streamlit 페이지 설정
st.set_page_config(page_title="KOSPI 200 Simulation", layout="wide")

# 제목
st.title("KOSPI 200 Simulation Results")

# 사이드바 설정
st.sidebar.header("Simulation Settings")

# 사용자 입력
user_name = st.sidebar.text_input("User Name", value="홍석문")
start_date = st.sidebar.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", value=date(2024, 12, 1))
target_trade_value_krw = st.sidebar.number_input("Target Trade Value (KRW)", value=1000000, step=100000)


query = """
        SELECT 종목코드, 종목이름 FROM fsts.kospi200 ORDER BY 종목이름 COLLATE "ko_KR";
    """

params = {}

with get_db_session() as db:
    result = sql_executor.execute_select(db, query, params)

    # Dropdown 메뉴를 통해 데이터 선택
    symbol_options = {
        # "삼성전자": "352820",
        # "대한항공": "003490",
    }

    for stock in result:
        key = stock['종목이름']  # 'a' 값을 키로
        value = stock['종목코드']  # 'b' 값을 값으로
        symbol_options[key] = value  # 딕셔너리에 추가
# 종목 선택
trading_logic_options = {
    "꼬리 확인": "check_wick",
    "관통형": "penetrating",
    "상승장악형1": "engulfing",
    "상승장악형2": "engulfing2",
    "상승반격형": "counterattack",
    "상승잉태형": "harami",
    "상승도지스타": "doji_star",
    "rsi 확인": "rsi_trading"
}

selected_trading_logic = st.sidebar.selectbox("select the trading logic:", list(trading_logic_options.keys()))
selected_stock = st.sidebar.selectbox("Select a Stock", list(symbol_options.keys()))
symbol = symbol_options[selected_stock]
trading_logic = trading_logic_options[selected_trading_logic]

# AutoTradingBot 및 SQLExecutor 객체 생성
auto_trading_stock = AutoTradingBot(user_name=user_name, virtual=True)


# 시뮬레이션 실행 버튼
if st.sidebar.button("Run Simulation"):
    st.write(f"Running simulation for stock: {selected_stock}...")
    
    try:
        # 시뮬레이션 실행
        simulation_plot = auto_trading_stock.simulate_trading(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            target_trade_value_krw=target_trade_value_krw,
            trading_logic=trading_logic
        )
        
        fig, ax = simulation_plot

        # 그래프 출력
        # st.pyplot(fig)
        
        # 그래프 이미지를 메모리에 저장
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)  # 메모리 절약을 위해 그래프 닫기
        
        image = buf
        
        # 이미지 표시
        st.image(image, caption=f"Graph for {selected_stock}", use_container_width=True)
        
        # DB에서 trading_history 결과 조회
        query = """
            SELECT *
            FROM fsts.simulation_history
            WHERE symbol = :symbol
            ORDER BY created_at DESC
            LIMIT 1
        """
        params = {"symbol": symbol}
        
        with get_db_session() as db:
            result = sql_executor.execute_select(db, query, params)
        print(result)
        if result:
            history_df = pd.DataFrame(result)
            # 순서대로 컬럼 정렬 (없는 컬럼은 무시)
            
            # 원하는 컬럼 순서 지정
            reorder_columns = [
                "symbol", "trading_logic", "average_price",
                "realized_pnl", "unrealized_pnl", "total_cost",
                "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity","history", "created_at"
            ]
            history_df = history_df[[col for col in reorder_columns if col in history_df.columns]]

            # 데이터의 행과 열 전환 (Transpose)
            history_df_transposed = history_df.transpose()
            # 컬럼 이름을 'Field', 'Value'로 변경
            history_df_transposed = history_df_transposed.rename_axis("Field").reset_index()
            history_df_transposed.columns = ["Field", "Value"]

            # 테이블 표시
            st.subheader("Trading History")
            st.dataframe(history_df_transposed,use_container_width=True)
            
            # history 컬럼에서 데이터 추출
            if not history_df.empty and "history" in history_df.columns:
                # history 컬럼의 값 가져오기
                trade_history = history_df.loc[0, "history"]

                try:
                    # trade_history가 문자열이면 JSON으로 변환
                    if isinstance(trade_history, str):
                        trade_history = json.loads(trade_history)
                    
                    # trade_history가 리스트인지 확인 후 DataFrame으로 변환
                    if isinstance(trade_history, list):
                        trade_history_df = pd.DataFrame(trade_history)
                        
                        # Streamlit 테이블로 표시
                        st.subheader("Detailed Trade History")
                        st.dataframe(trade_history_df, use_container_width=True)
                    else:
                        st.error(f"The 'history' field is not a valid list. Current type: {type(trade_history)}")
                except json.JSONDecodeError as e:
                    st.error(f"Failed to decode 'history' field as JSON: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
            else:
                st.write("No history field found in the result.")

            
        else:
            st.write("No trading history found in the database for this stock.")

    except Exception as e:
        st.error(f"An error occurred during the simulation: {e}")
