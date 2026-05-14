import os
import smtplib
import traceback
import pandas as pd
import numpy as np
import pandas_ta as ta
import yfinance as yf

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
    msg["Subject"] = Header("台股量化3.0回測報告", "utf-8")
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
# 產生策略信號
# =========================
def generate_signal(df):

    df["RSI"] = ta.rsi(df["Close"], 14)

    macd = ta.macd(df["Close"])
    df["MACD"] = macd["MACD_12_26_9"]
    df["MACDs"] = macd["MACDs_12_26_9"]

    df["SMA20"] = ta.sma(df["Close"], 20)
    df["SMA60"] = ta.sma(df["Close"], 60)

    df["VOL20"] = ta.sma(df["Volume"], 20)

    signal = []

    for i in range(len(df)):

        if i < 60:
            signal.append(0)
            continue

        row = df.iloc[i]

        score = 0

        if row["Close"] > row["SMA20"]:
            score += 1

        if row["SMA20"] > row["SMA60"]:
            score += 1

        if row["RSI"] > 50:
            score += 1

        if row["MACD"] > row["MACDs"]:
            score += 1

        if row["Volume"] > row["VOL20"]:
            score += 1

        # 進場條件
        signal.append(1 if score >= 4 else 0)

    df["signal"] = signal
    return df


# =========================
# 回測
# =========================
def backtest(df):

    position = 0
    buy_price = 0

    returns = []
    trades = 0
    wins = 0

    for i in range(len(df)):

        price = df["Close"].iloc[i]
        sig = df["signal"].iloc[i]

        # 進場
        if sig == 1 and position == 0:
            position = 1
            buy_price = price
            trades += 1

        # 出場
        elif sig == 0 and position == 1:
            ret = (price - buy_price) / buy_price
            returns.append(ret)

            if ret > 0:
                wins += 1

            position = 0

    if not returns:
        return None

    total_return = np.sum(returns)
    win_rate = wins / trades if trades > 0 else 0
    max_dd = np.min(returns)

    return {
        "總報酬": round(total_return * 100, 2),
        "勝率": round(win_rate * 100, 2),
        "交易次數": trades,
        "平均交易": round(np.mean(returns) * 100, 2),
        "最大單筆虧損": round(max_dd * 100, 2)
    }


# =========================
# Main
# =========================
if __name__ == "__main__":

    results = []

    stocks = get_stocks()

    for s in stocks:

        try:
            print(f"回測 {s}")

            df = yf.Ticker(f"{s}.TW").history(period="1y")

            if df.empty or len(df) < 120:
                continue

            df = generate_signal(df)
            result = backtest(df)

            if not result:
                continue

            result["股票"] = s

            results.append(result)

        except:
            traceback.print_exc()

    if not results:
        print("無回測結果")
        exit()

    df = pd.DataFrame(results)

    df = df.sort_values("總報酬", ascending=False)

    content = "🔥 台股量化3.0 回測 TOP策略\n\n"
    content += df.to_string(index=False)

    send_email(content)

    print(df)
