import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.auto_trading_bot import AutoTradingBot

url = os.environ.get("SIMULATION_DATA_S3_PATH")

print(f'path = {url}')

# auto_trading_stock = AutoTradingBot(id=simulation_data["user_id"], virtual=False)
# simulation_data["start_date"] = datetime.fromisoformat(simulation_data["start_date"])
# simulation_data["end_date"] = datetime.fromisoformat(simulation_data["end_date"])

# results, failed_stocks = auto_trading_stock.simulate_trading_bulk(simulation_data)