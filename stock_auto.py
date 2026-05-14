import os
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time

# =========================
# LINE Bot
# =========================
def send_line(msg):

    token = os.environ.get("LINE_TOKEN")
    user = os.environ.get("LINE_USER_ID")

    if not token or not user:
        print("❌ LINE 設定缺失")
        return

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": user,
        "messages": [{"type": "text", "text": msg[:1000]}]
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print("LINE status:", r.status_code)

    except Exception as e:
        print("LINE error:", e)


# =========================
# 股票池
# =========================
stocks = [
    "2330","2317","2454","2382","2412",
    "2303","2603","2609","2615","2881",
    "2882","2891","3711","3231","2379"
]

print("🚀 START SCANNER")
print("stocks:", stocks)


# =========================
# 主流程
# =========================
results = []

for i, s in enumerate(stocks):

    try:
        print(f"\n📊 [{i+1}/{len(stocks)}] {s} loading...")

        df = yf.Ticker(f"{s}.TW").history(period="6mo", timeout=15)

        if df is None or df.empty:
            print("❌ no data")
            continue

        if len(df) < 60:
            print("❌ not enough data")
            continue

        print("✔ data ok")

        # indicators
        df["RSI"] = ta.rsi(df["Close"], 14)

        macd = ta.macd(df["Close"])
        df["MACD"] = macd["MACD_12_26_9"]
        df["MACDs"] = macd["MACDs_12_26_9"]

        df["SMA20"] = ta.sma(df["Close"], 20)
        df["SMA60"] = ta.sma(df["Close"], 60)

        last = df.iloc[-1]

        score = 0
        if last["Close"] > last["SMA20"]:
            score += 2
        if last["SMA20"] > last["SMA60"]:
            score += 2
        if last["RSI"] > 50:
            score += 1
        if last["MACD"] > last["MACDs"]:
            score += 2

        print("score:", score)

        results.append({
            "stock": s,
            "score": score,
            "price": round(last["Close"], 2)
        })

        time.sleep(0.3)

    except Exception as e:
        print("❌ error:", s, e)


print("\n====================")
print("results:", len(results))


# =========================
# fallback（避免空）
# =========================
if len(results) == 0:
    print("⚠️ fallback triggered")
    results = [{"stock":"2330","score":1,"price":0}]


# =========================
# sort
# =========================
df = pd.DataFrame(results).sort_values("score", ascending=False)

msg = "📊 台股量化穩定版\n\n"

for i, r in df.iterrows():
    msg += f"{i+1}. {r['stock']} 分數:{r['score']} 價格:{r['price']}\n"

print("\n📩 sending LINE...")
send_line(msg)

print("\n✅ DONE")
