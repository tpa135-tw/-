import os
import smtplib
import traceback
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import feedparser

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
    msg["Subject"] = Header("📱 台股量化3.2（手機簡版）", "utf-8")
    msg["From"] = user
    msg["To"] = user

    server = smtplib.SMTP("smtp.mail.yahoo.com", 587)
    server.starttls()
    server.login(user, pwd)
    server.send_message(msg)
    server.quit()


# =========================
# 股票池
# =========================
def get_stocks():

    return [
        "2330","2317","2454","2382","2412",
        "2303","2603","2609","2615","2881",
        "2882","2891","3711","3231","2379"
    ]


# =========================
# 分數模型（簡化）
# =========================
def score_stock(df):

    score = 0

    last = df.iloc[-1]

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

    return score


# =========================
# 風險判斷（超簡化）
# =========================
def risk_level(rsi):

    if rsi > 75:
        return "🔴 高風險"
    elif rsi > 60:
        return "🟡 中風險"
    else:
        return "🟢 低風險"


# =========================
# Main
# =========================
if __name__ == "__main__":

    results = []

    stocks = get_stocks()

    for s in stocks:

        try:
            df = yf.Ticker(f"{s}.TW").history(period="6mo")

            if df.empty or len(df) < 60:
                continue

            # 指標
            df["RSI"] = ta.rsi(df["Close"], 14)

            macd = ta.macd(df["Close"])
            df["MACD"] = macd["MACD_12_26_9"]
            df["MACDs"] = macd["MACDs_12_26_9"]

            df["SMA20"] = ta.sma(df["Close"], 20)
            df["SMA60"] = ta.sma(df["Close"], 60)
            df["VOL20"] = ta.sma(df["Volume"], 20)

            score = score_stock(df)

            rsi = df["RSI"].iloc[-1]

            # 過濾太弱
            if score < 3:
                continue

            results.append({
                "股票": s,
                "分數": score,
                "價格": round(df["Close"].iloc[-1], 2),
                "風險": risk_level(rsi)
            })

        except:
            traceback.print_exc()

    if not results:
        print("無資料")
        exit()

    df = pd.DataFrame(results)
    df = df.sort_values("分數", ascending=False).head(10)

    # =========================
    # 📱手機友善文字表格
    # =========================

    content = "📱 台股量化3.2（手機簡版）\n"
    content += "================================\n\n"

    content += "排名  股票   分數  價格   風險\n"
    content += "--------------------------------\n"

    for i, row in df.iterrows():

        content += f"{i+1:>2}   {row['股票']}   {row['分數']:>2}   {row['價格']:>6}   {row['風險']}\n"

    content += "\n================================\n"
    content += "說明：分數越高 → 趨勢越強\n"

    send_email(content)

    print(df)
