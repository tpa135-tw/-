import requests

def send_line(content):

    token = os.environ.get("LINE_TOKEN")

    if not token:
        print("缺 LINE_TOKEN")
        return

    url = "https://notify-api.line.me/api/notify"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    data = {
        "message": content
    }

    try:
        res = requests.post(url, headers=headers, data=data)

        print("LINE status:", res.status_code)

    except Exception as e:
        print("LINE error:", e)
