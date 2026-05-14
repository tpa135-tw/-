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
        print("缺 Email 環境變數")
        return

    try:
        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = Header("台股量化2.0選股報告", "utf-8")
        msg["From"] = user
        msg["To"] = user

        server = smtplib.SMTP("smtp.mail.yahoo.com", 587)
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
        server.quit()

        print("Email 已寄出")

    except Exception as e:
        print(f"Email錯誤: {e}")
        traceback.print_exc()


# =========================
# 股票池（熱門 + 流動性）
# =========================
def get_universe():

    return [
        "2330","2317","2454","2382","2412",
        "2303","2408","2603","2609","2615",
        "2881","2882","2891","3711","3231",
        "2379","2357","2353","2383","2409",
        "2308","2301","2302","6669","6446"
    ]


# =========================
# 新聞分數
# =========================
def news_score(stock):

    pos = ["AI","成長","創高","訂單","擴產","NVIDIA"]
    neg = ["虧損","下修","賣超","衰退","利空"]

    score = 0

    try:
        url = f"https://news.google.com/rss/search?q={stock}+台股"
        feed = feedparser.parse(url)

        for e in feed.entries[:5]:
            t = e.title

            for w in pos:
                if w in t:
                    score += 3

            for w in neg:
                if w in t:
                    score -= 3

    except:
        pass

    return score


# =========================
# 技術分數（量化核心）
# =========================
def tech_score(df):

    score = 0

    try:
        last = df.iloc[-1]

        # 趨勢
        if last["Close"] > last["SMA20"]:
            score += 15

        if last["SMA20"] > last["SMA60"]:
            score += 15

        # 動能
        if last["RSI"] > 50:
            score += 10

        if last["MACD"] > last["MACDs"]:
            score += 15

        # 成交量
        if last["Volume"] > last["VOL_SMA20"]:
            score += 10

        # 避免過熱
        if last["RSI"] > 75:
            score -= 10

    except:
        pass

    return score


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    results = []

    stocks = get_universe()

    for s in stocks:

        try:
            print(f"分析 {s}")

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
            df["VOL_SMA20"] = ta.sma(df["Volume"], 20)

            tech = tech_score(df)
            news = news_score(s)

            total = tech + news

            # 過濾弱勢股
            if total < 20:
                continue

            results.append({
                "股票": s,
                "收盤": round(df["Close"].iloc[-1], 2),
                "技術": tech,
                "新聞": news,
                "總分": total
            })

        except:
            traceback.print_exc()

    if not results:
        print("無結果")
        exit()

    df = pd.DataFrame(results)
    df = df.sort_values("總分", ascending=False).head(10)

    content = "🔥 台股量化2.0 TOP10\n\n"
    content += df.to_string(index=False)

    send_email(content)

    print(df)
