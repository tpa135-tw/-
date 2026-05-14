import os
import smtplib
import traceback
import pandas as pd
import pandas_ta as ta
import feedparser
import requests

from email.mime.text import MIMEText
from email.header import Header


# =========================
# Email
# =========================
def send_email(content):

    user = os.environ.get("YAHOO_EMAIL")
    pwd = os.environ.get("YAHOO_PASSWORD")

    if not user or not pwd:
        print("缺 Email")
        return

    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = Header("📊 台股量化穩定版 4.0", "utf-8")
    msg["From"] = user
    msg["To"] = user

    server = smtplib.SMTP("smtp.mail.yahoo.com", 587)
    server.starttls()
    server.login(user, pwd)
    server.send_message(msg)
    server.quit()


# =========================
# 穩定股票池
# =========================
def get_stocks():

    return [
        "2330","2317","2454","2382","2412",
        "2303","2603","2609","2615","2881",
        "2882","2891","3711","3231","2379"
    ]


# =========================
# 🔥 Stooq 抓資料（穩定）
# =========================
def get_data_stooq(stock):

    try:
        url = f"https://stooq.com/q/d/l/?s={stock}.tw&i=d"

        df = pd.read_csv(url)

        if df.empty:
            return None

        df = df.rename(columns={
            "Date": "date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume"
        })

        df = df.dropna()

        return df

    except:
        return None


# =========================
# Yahoo fallback
# =========================
def get_data_yahoo(stock):

    try:
        import yfinance as yf

        df = yf.Ticker(f"{stock}.TW").history(period="6mo")

        if df is None or df.empty:
            return None

        return df.reset_index()

    except:
        return None


# =========================
# 安全抓資料
# =========================
def get_data(stock):

    df = get_data_stooq(stock)

    if df is None or len(df) < 60:
        df = get_data_yahoo(stock)

    if df is None or len(df) < 60:
        print(f"{stock} 無資料（跳過）")
        return None

    return df


# =========================
# 分數模型
# =========================
def score(df):

    last = df.iloc[-1]

    score = 0

    try:
        df["RSI"] = ta.rsi(df["Close"], 14)

        macd = ta.macd(df["Close"])
        df["MACD"] = macd["MACD_12_26_9"]
        df["MACDs"] = macd["MACDs_12_26_9"]

        df["SMA20"] = ta.sma(df["Close"], 20)
        df["SMA60"] = ta.sma(df["Close"], 60)

        df["VOL20"] = ta.sma(df["Volume"], 20)

        if last["Close"] > last["SMA20"]:
            score += 2

        if last["SMA20"] > last["SMA60"]:
            score += 2

        if last["RSI"] > 50:
            score += 1

        if last["MACD"] > last["MACDs"]:
            score += 2

        if last["Volume"] > last["VOL20"]:
            score += 1

    except:
        pass

    return score


# =========================
# 風險
# =========================
def risk(rsi):

    if rsi > 75:
        return "🔴"
    elif rsi > 60:
        return "🟡"
    else:
        return "🟢"


# =========================
# Main
# =========================
if __name__ == "__main__":

    results = []

    stocks = get_stocks()

    print("stocks:", stocks)

    for s in stocks:

        try:
            df = get_data(s)

            if df is None:
                continue

            s_score = score(df)

            if "RSI" not in df:
                df["RSI"] = ta.rsi(df["Close"], 14)

            rsi = df["RSI"].iloc[-1]

            results.append({
                "股票": s,
                "分數": s_score,
                "價格": round(df["Close"].iloc[-1], 2),
                "風險": risk(rsi)
            })

        except:
            traceback.print_exc()

    print("results:", len(results))

    # =========================
    # 保底機制（避免空結果）
    # =========================
    if len(results) == 0:

        print("⚠️ 無資料，啟用保底")

        results = [{
            "股票": "2330",
            "分數": 1,
            "價格": 0,
            "風險": "🟢"
        }]

    df = pd.DataFrame(results)
    df = df.sort_values("分數", ascending=False).head(10)

    # =========================
    # 📱手機簡訊風格 Email
    # =========================
    content = "📊 台股量化穩定版4.0\n"
    content += "====================\n"
    content += "排名 股票 分數 價格 風險\n"
    content += "--------------------\n"

    for i, row in df.iterrows():
        content += f"{i+1} {row['股票']} {row['分數']} {row['價格']} {row['風險']}\n"

    send_email(content)

    print(df)
