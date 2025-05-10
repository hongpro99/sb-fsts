from pydantic import BaseModel
from typing import Dict, Optional, List


class SimulationTradingBulkModel(BaseModel):
    user_id: str
    start_date: str
    end_date: str
    target_trade_value_krw: int
    target_trade_value_ratio: Optional[float]
    selected_stocks: List[str]
    selected_symbols: Dict[str, str]
    interval: str
    buy_trading_logic: Optional[List[str]]
    sell_trading_logic: Optional[List[str]]
    buy_condition_yn: bool
    buy_percentage: float
    initial_capital: float
    rsi_buy_threshold: int
    rsi_sell_threshold: int
    rsi_period: int
    use_take_profit: bool
    take_profit_ratio: float
    use_stop_loss: bool
    stop_loss_ratio: float