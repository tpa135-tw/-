import requests
import os

def send_line(message):

    token = os.environ.get("LINE_TOKEN")  # 改成 Channel Access Token

    if not token:
        print("缺 LINE_TOKEN")
        return

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "to": os.environ.get("LINE_USER_ID"),  # 你自己的 user id
        "messages": [
            {
                "type": "text",
                "text": message[:1000]
            }
        ]
    }

    res = requests.post(url, headers=headers, json=payload)

    print("LINE status:", res.status_code)
    print(res.text)
