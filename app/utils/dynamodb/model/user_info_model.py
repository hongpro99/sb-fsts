from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, ListAttribute, BooleanAttribute
import time
import uuid


class UserInfo(Model):
    class Meta:
        table_name = "fsts-user-info"
        region = "ap-northeast-2"

    id = UnicodeAttribute(hash_key=True)  # ✅ PK
    created_at = NumberAttribute()
    updated_at = NumberAttribute(null=True)
    password = UnicodeAttribute()
    name = UnicodeAttribute()
    app_key = UnicodeAttribute()
    secret_key = UnicodeAttribute()
    kis_id = UnicodeAttribute()
    account = UnicodeAttribute()
    virtual_kis_id =  UnicodeAttribute(null=True)
    virtual_app_key =  UnicodeAttribute(null=True)
    virtual_secret_key =  UnicodeAttribute(null=True)
    virtual_account =  UnicodeAttribute(null=True)
    buy_trading_logic = ListAttribute(of=UnicodeAttribute)
    sell_trading_logic = ListAttribute(of=UnicodeAttribute)
    target_trade_value_krw = NumberAttribute()
    max_allocation = NumberAttribute()
    interval = UnicodeAttribute()
    take_profit_threshold = NumberAttribute(null=True)  # 예: 0.05
    stop_loss_threshold = NumberAttribute(null=True)    # 예: -0.05
    use_take_profit = BooleanAttribute(null=True)       # 예: True
    use_stop_loss = BooleanAttribute(null=True)         # 예: True
    trading_bot_name = UnicodeAttribute(null=True)