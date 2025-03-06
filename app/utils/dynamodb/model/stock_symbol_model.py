from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
import time
import uuid


class StockSymbol(Model):
    class Meta:
        table_name = "fsts-stock-symbol"
        region = "ap-northeast-2"

    symbol = UnicodeAttribute(hash_key=True)  # ✅ PK
    created_at = NumberAttribute()
    updated_at = NumberAttribute(null=True)
    symbol_name = UnicodeAttribute()
    type = UnicodeAttribute() #kospi, kosdac