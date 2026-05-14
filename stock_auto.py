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
# Yahoo Email 發送
# =========================
def send_yahoo_email(content):

    email_user = os.environ.get('YAHOO_EMAIL')
    email_password = os.environ.get('YAHOO_PASSWORD')

    if not email_user or not email_password:
        print("未偵測到 Email 環境變數")
        return

    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header('台股 AI 自動選股報告', 'utf-8')
        msg['From'] = email_user
        msg['To'] = email_user

        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()

        print('Email 已成功送出至 Yahoo 信箱')

    except Exception as e:
        print(f'Email 發送錯誤: {e}')
        traceback.print_exc()


# =========================
# 新聞分析
# =========================
def analyze_news(stock):

    positive_keywords = ["AI", "成長", "創高", "擴產", "訂單", "買超", "利多", "調升", "NVIDIA", "CoWoS"]
    negative_keywords = ["虧損", "衰退", "賣超", "下修", "裁員", "利空"]

    score = 0
    news_list = []

    try:
        url = f"https://news.google.com/rss/search?q={stock}+台股"
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            title = entry.title
            news_list.append(title)

            for w in positive_keywords:
                if w in title:
                    score += 3

            for w in negative_keywords:
                if w in title:
                    score -= 3

    except Exception as e:
        print(f"{stock} 新聞分析失敗: {e}")

    return score, news_list[:3]


# =========================
# 技術分析
# =========================
def technical_score(df):

    score = 0

    try:
        latest = df.iloc[-1]

        if latest["RSI"] > 50:
            score += 15

        if latest["MACD"] > latest["MACDs"]:
            score += 15

        if latest["Close"] > latest["SMA20"]:
            score += 15

        if latest["Close"] > latest["SMA60"]:
            score += 15

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

    # ===== 修正：GitHub 路徑問題 =====
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "stock_list.txt")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            stocks = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"讀取 stock_list.txt 失敗: {e}")
        exit()

    # =========================
    # 股票分析
    # =========================
    for stock in stocks:

        try:
            print(f"開始分析 {stock}")

            ticker = yf.Ticker(f"{stock}.TW")
            df = ticker.history(period="6mo")

            if df.empty or len(df) < 60:
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

            latest_price = round(df["Close"].iloc[-1], 2)

            day_change = round(
                (df["Close"].iloc[-1] - df["Close"].iloc[-2])
                / df["Close"].iloc[-2] * 100,
                2
            )

            if day_change > 7:
                print(f"{stock} 漲幅過大")
                continue

            tech_score = technical_score(df)
            news_score, news = analyze_news(stock)

            total_score = tech_score + news_score

            results.append({
                "股票": stock,
                "收盤": latest_price,
                "漲跌%": day_change,
                "技術分": tech_score,
                "新聞分": news_score,
                "總分": total_score,
                "新聞": " | ".join(news)
            })

            print(f"{stock} 完成")

        except Exception:
            print(f"{stock} 發生錯誤")
            traceback.print_exc()

    # 無資料
    if not results:
        print("無符合條件股票")
        exit()

    # =========================
    # 結果整理
    # =========================
    df_final = pd.DataFrame(results)
    df_final = df_final.sort_values(by="總分", ascending=False).head(10)

    df_final.to_csv("stock_report.csv", index=False, encoding="utf-8-sig")

    # =========================
    # Email
    # =========================
    content = "今日 AI 台股觀察名單\n\n" + df_final.to_string(index=False)

    send_yahoo_email(content)

    print(df_final)
