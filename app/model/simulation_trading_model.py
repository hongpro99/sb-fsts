from pydantic import BaseModel
from typing import Dict, Optional, List


class SimulationTradingModel(BaseModel):
    user_id: str
    symbol: str
    start_date: str
    end_date: str
    target_trade_value_krw: int
    buy_trading_logic: Optional[List[str]]
    sell_trading_logic: Optional[List[str]]
    interval: str
    buy_percentage: Optional[float]
    ohlc_mode: Optional[str]
    rsi_buy_threshold: int
    rsi_sell_threshold: int
    rsi_period: int
    initial_capital: float
    use_take_profit: bool
    take_profit_ratio: float
    use_stop_loss: bool
    stop_loss_ratio: float