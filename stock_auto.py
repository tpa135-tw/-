import os
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf

# =========================
# LINE 推播
# =========================
def send_line(message):

    token = os.environ.get("LINE_TOKEN")

    if not token:
        print("❌ 缺 LINE_TOKEN")
        return

    url = "https://notify-api.line.me/api/notify"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    data = {
        "message": message[:900]  # 防止超過 LINE 字數限制
    }

    try:
        res = requests.post(url, headers=headers, data=data)
        print("LINE status:", res.status_code)

    except Exception as e:
        print("LINE error:", e)


# =========================
# 股票池（穩定版）
# =========================
def get_stocks():

    return [
        "2330","2317","2454","2382","2412",
        "2303","2603","2609","2615","2881",
        "2882","2891","3711","3231","2379"
    ]


# =========================
# 分數模型
# =========================
def score(df):

    last = df.iloc[-1]
    s = 0

    if last["Close"] > last["SMA20"]:
        s += 2

    if last["SMA20"] > last["SMA60"]:
        s += 2

    if last["RSI"] > 50:
        s += 1

    if last["MACD"] > last["MACDs"]:
        s += 2

    if last["Volume"] > last["VOL20"]:
        s += 1

    return s


# =========================
# 風險等級
# =========================
def risk(rsi):

    if rsi > 75:
        return "🔴高"
    elif rsi > 60:
        return "🟡中"
    else:
        return "🟢低"


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    stocks = get_stocks()
    results = []

    print("stocks:", stocks)

    for s in stocks:

        try:
            df = yf.Ticker(f"{s}.TW").history(period="6mo")

            if df is None or df.empty or len(df) < 60:
                continue

            # 指標
            df["RSI"] = ta.rsi(df["Close"], 14)

            macd = ta.macd(df["Close"])
            df["MACD"] = macd["MACD_12_26_9"]
            df["MACDs"] = macd["MACDs_12_26_9"]

            df["SMA20"] = ta.sma(df["Close"], 20)
            df["SMA60"] = ta.sma(df["Close"], 60)
            df["VOL20"] = ta.sma(df["Volume"], 20)

            sc = score(df)
            rsi = df["RSI"].iloc[-1]

            # 太弱直接跳過
            if sc < 3:
                continue

            results.append({
                "股票": s,
                "分數": sc,
                "價格": round(df["Close"].iloc[-1], 2),
                "風險": risk(rsi)
            })

        except:
            continue

    print("results:", len(results))

    # =========================
    # 保底（避免空結果）
    # =========================
    if len(results) == 0:

        results = [{
            "股票": "2330",
            "分數": 1,
            "價格": 0,
            "風險": "🟢"
        }]

    df = pd.DataFrame(results)
    df = df.sort_values("分數", ascending=False).head(10)

    # =========================
    # LINE 文字格式（手機友善）
    # =========================
    msg = "📊 台股量化 LINE選股\n"
    msg += "====================\n"
    msg += "排名 股票 分數 價格 風險\n"
    msg += "--------------------\n"

    for i, row in df.iterrows():
        msg += f"{i+1} {row['股票']} {row['分數']} {row['價格']} {row['風險']}\n"

    msg += "\n📌 分數越高＝趨勢越強"

    # =========================
    # 推播 LINE
    # =========================
    send_line(msg)

    print(df)
