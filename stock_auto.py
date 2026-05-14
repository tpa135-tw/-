import os
import smtplib
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import feedparser
import traceback

from email.mime.text import MIMEText
from email.header import Header

# =========================
# Email 發送
# =========================
def send_yahoo_email(content):

    email_user = os.environ.get("YAHOO_EMAIL")
    email_password = os.environ.get("YAHOO_PASSWORD")

    if not email_user or not email_password:
        print("未設定 Yahoo 環境變數")
        return

    msg = MIMEText(content, "plain", "utf-8")

    msg["Subject"] = Header("台股 AI 自動選股報告", "utf-8")
    msg["From"] = email_user
    msg["To"] = email_user

    try:

        server = smtplib.SMTP("smtp.mail.yahoo.com", 587)

        server.starttls()

        server.login(email_user, email_password)

        server.send_message(msg)

        server.quit()

        print("Email 發送成功")

    except Exception as e:

        print(f"Email 發送失敗: {e}")


# =========================
# 新聞情緒分析
# =========================
def analyze_news(stock):

    positive_keywords = [
        "AI",
        "成長",
        "創高",
        "擴產",
        "訂單",
        "外資買超",
        "調升",
        "利多",
        "CoWoS",
        "NVIDIA"
    ]

    negative_keywords = [
        "下修",
        "賣超",
        "衰退",
        "虧損",
        "利空",
        "裁員"
    ]

    score = 0

    news_list = []

    try:

        url = f"https://news.google.com/rss/search?q={stock}+台股"

        feed = feedparser.parse(url)

        entries = feed.entries[:10]

        for entry in entries:

            title = entry.title

            news_list.append(title)

            for word in positive_keywords:

                if word in title:
                    score += 3

            for word in negative_keywords:

                if word in title:
                    score -= 3

    except Exception as e:

        print(f"{stock} 新聞分析錯誤: {e}")

    return score, news_list[:3]


# =========================
# 技術分析
# =========================
def technical_score(df):

    score = 0

    latest = df.iloc[-1]

    try:

        # RSI
        if latest["RSI"] > 50:
            score += 15

        # MACD
        if latest["MACD"] > latest["MACDs"]:
            score += 15

        # 站上月線
        if latest["Close"] > latest["SMA20"]:
            score += 15

        # 站上季線
        if latest["Close"] > latest["SMA60"]:
            score += 15

        # 成交量放大
        if latest["Volume"] > latest["VOL_SMA20"]:
            score += 10

    except:
        pass

    return score


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    results = []

    try:

        with open("stock_list.txt", "r") as f:

            stocks = [line.strip() for line in f.readlines()]

    except Exception as e:

        print(f"讀取 stock_list.txt 失敗: {e}")

        exit()

    for stock in stocks:

        try:

            print(f"開始分析 {stock}")

            ticker = yf.Ticker(f"{stock}.TW")

            df = ticker.history(
                period="6mo",
                auto_adjust=False
            )

            # 防呆
            if df.empty:
                print(f"{stock} 無資料")
                continue

            if len(df) < 60:
                print(f"{stock} 資料不足")
                continue

            # 技術指標
            df["RSI"] = ta.rsi(df["Close"], length=14)

            macd = ta.macd(df["Close"])

            df["MACD"] = macd["MACD_12_26_9"]

            df["MACDs"] = macd["MACDs_12_26_9"]

            df["SMA20"] = ta.sma(df["Close"], length=20)

            df["SMA60"] = ta.sma(df["Close"], length=60)

            df["VOL_SMA20"] = ta.sma(df["Volume"], length=20)

            # 昨日收盤
            latest_price = round(df["Close"].iloc[-1], 2)

            # 昨日漲跌幅
            day_change = round(
                (
                    (
                        df["Close"].iloc[-1]
                        - df["Close"].iloc[-2]
                    )
                    / df["Close"].iloc[-2]
                ) * 100,
                2
            )

            # 過熱排除
            if day_change > 7:
                print(f"{stock} 漲太多，跳過")
                continue

            # 技術分
            tech_score = technical_score(df)

            # 新聞分
            news_score, news = analyze_news(stock)

            # 總分
            total_score = tech_score + news_score

            results.append({

                "股票": stock,
                "昨日收盤": latest_price,
                "漲跌幅%": day_change,
                "技術分": tech_score,
                "新聞分": news_score,
                "總分": total_score,
                "近期消息": " | ".join(news)

            })

            print(f"{stock} 完成")

        except Exception as e:

            print(f"{stock} 發生錯誤")

            traceback.print_exc()

    # 沒資料
    if len(results) == 0:

        print("今日無符合條件股票")

        exit()

    # DataFrame
    df_final = pd.DataFrame(results)

    # 排序
    df_final = df_final.sort_values(
        by="總分",
        ascending=False
    ).head(10)

    # 儲存 CSV
    df_final.to_csv(
        "stock_report.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Email內容
    content = "今日 AI 台股觀察名單\n\n"

    content += df_final.to_string(index=False)

    # 寄送
    send_yahoo_email(content)

    print(df_final)
