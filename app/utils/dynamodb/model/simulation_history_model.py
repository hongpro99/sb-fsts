from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
import time
import uuid


class SimulationHistory(Model):
    class Meta:
        table_name = "fsts-simulation-history"
        region = "ap-northeast-2"

    symbol = UnicodeAttribute(hash_key=True)  # ✅ PK
    created_at = NumberAttribute(range_key=True)  # ✅ SK (밀리세컨드 단위)
    updated_at = NumberAttribute(null=True)
    average_price = NumberAttribute()
    realized_pnl = NumberAttribute()
    unrealized_pnl = NumberAttribute()
    realized_roi = NumberAttribute()
    unrealized_roi = NumberAttribute()
    total_cost = NumberAttribute()
    total_quantity = NumberAttribute()
    buy_count = NumberAttribute()
    sell_count = NumberAttribute()
    buy_dates = UnicodeAttribute()
    sell_dates = UnicodeAttribute()
    history = UnicodeAttribute(null=True)
