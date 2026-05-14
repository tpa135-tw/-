import os
import smtplib
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
import feedparser

from email.mime.text import MIMEText
from email.header import Header

# =========================
# Email
# =========================
def send_yahoo_email(content):

    email_user = os.environ.get('YAHOO_EMAIL')
    email_password = os.environ.get('YAHOO_PASSWORD')

    if not email_user or not email_password:
        print("找不到 Email 環境變數")
        return

    msg = MIMEText(content, 'plain', 'utf-8')

    msg['Subject'] = Header('台股 AI 自動選股報告', 'utf-8')
    msg['From'] = email_user
    msg['To'] = email_user

    try:
        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)

        server.starttls()

        server.login(email_user, email_password)

        server.send_message(msg)

        server.quit()

        print("Email 發送成功")

    except Exception as e:
        print(f"Email 發送失敗: {e}")

# =========================
# 新聞分析
# =========================
def analyze_news(stock):

    keywords_positive = [
        'AI',
        '營收成長',
        '創高',
        '擴廠',
        '訂單',
        '外資買超',
        'CoWoS',
        'NVIDIA',
        '法說利多',
        '調升目標價'
    ]

    score = 0

    news_summary = []

    try:

        url = f"https://news.google.com/rss/search?q={stock}+台股"

        feed = feedparser.parse(url)

        entries = feed.entries[:10]

        for entry in entries:

            title = entry.title

            news_summary.append(title)

            for keyword in keywords_positive:

                if keyword in title:
                    score += 4

    except Exception as e:

        print(f"{stock} 新聞錯誤: {e}")

    return score, news_summary[:3]

# =========================
# 技術分析
# =========================
def technical_score(df):

    score = 0

    latest = df.iloc[-1]

    # RSI
    if latest['RSI'] > 50:
        score += 15

    # MACD
    if latest['MACD'] > latest['MACDs']:
        score += 15

    # 站上20MA
    if latest['Close'] > latest['SMA20']:
        score += 15

    # 站上60MA
    if latest['Close'] > latest['SMA60']:
        score += 15

    return score

# =========================
# 主程式
# =========================
if __name__ == "__main__":

    results = []

    with open('stock_list.txt', 'r') as f:

        stocks = [line.strip() for line in f.readlines()]

    for stock in stocks:

        try:

            print(f"分析 {stock}")

            ticker = yf.Ticker(f"{stock}.TW")

            df = ticker.history(period="6mo")

            if len(df) < 60:
                continue

            # 指標
            df['RSI'] = ta.rsi(df['Close'], length=14)

            macd = ta.macd(df['Close'])

            df['MACD'] = macd['MACD_12_26_9']

            df['MACDs'] = macd['MACDs_12_26_9']

            df['SMA20'] = ta.sma(df['Close'], length=20)

            df['SMA60'] = ta.sma(df['Close'], length=60)

            # 技術分析
            tech_score = technical_score(df)

            # 新聞分析
            news_score, news = analyze_news(stock)

            total_score = tech_score + news_score

            latest_price = round(df['Close'].iloc[-1], 2)

            results.append({

                '股票': stock,
                '昨日收盤': latest_price,
                '技術分數': tech_score,
                '消息分數': news_score,
                '總分': total_score,
                '近期消息': ' | '.join(news)

            })

        except Exception as e:

            print(f"{stock} 錯誤: {e}")

    # 排序
    df_final = pd.DataFrame(results)

    df_final = df_final.sort_values(
        by='總分',
        ascending=False
    ).head(10)

    # 輸出CSV
    df_final.to_csv(
        'stock_report.csv',
        index=False,
        encoding='utf-8-sig'
    )

    # Email內容
    content = "今日 AI 台股觀察名單\n\n"

    content += df_final.to_string(index=False)

    # 發送Email
    send_yahoo_email(content)

    print(df_final)
