import numpy as np
import requests


class Webhook:
    
    def send_discord_webhook(self, message, bot_type):
        if bot_type == 'trading':
            webhook_url = 'https://discord.com/api/webhooks/1324331095583363122/wbpm4ZYV4gRZhaSywRp28ZWQrp_hJf8iiitISJrNYtAyt5NmBccYWAeYgcGd5pzh4jRK'  # 복사한 Discord 웹훅 URL로 변경
            username = "Stock Trading Bot"
        if bot_type == 'alarm':
            webhook_url = 'https://discord.com/api/webhooks/1313346849838596106/6Rn_8BNDeL9bMYfFtqscpu4hPah5c2RsNl0rBiPoSw_Qb9RXgDdVHoHmwEuStPv_ufnV'
            username = 'Stock Alarm Bot'
        data = {
            "content": message,
            "username": username,  # 원하는 이름으로 설정 가능
        }
        
        # 요청 보내기
        response = requests.post(webhook_url, json=data)
        
        # 응답 확인
        if response.status_code == 204:
            print("메시지가 성공적으로 전송되었습니다.")
        else:
            print(f"메시지 전송 실패: {response.status_code}, {response.text}")