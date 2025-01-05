from datetime import datetime, timedelta

class Condition:
    def __init__(self, ohlc_data):
        self.ohlc_data = ohlc_data

    def _find_data_by_offset(self, base_date, offset):
        """
        기준 날짜(base_date)로부터 offset일 전 데이터를 반환.
        """
        target_date = base_date - timedelta(days=offset)

        # 데이터 검색
        for data in self.ohlc_data:
            if data.time.date() == target_date.date():  # datetime 객체 비교
                return data
        return None

    def get_open(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.open if data else None

    def get_close(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.close if data else None

    def get_high(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.high if data else None

    def get_low(self, base_date, offset):
        data = self._find_data_by_offset(base_date, offset)
        return data.low if data else None
