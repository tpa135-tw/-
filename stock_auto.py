import os
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.header import Header

# ... 你的 tech_score 和 news_score 函數 ...

def send_email(top10_df):
    email = os.environ.get('YAHOO_EMAIL')
    password = os.environ.get('YAHOO_PASSWORD')
    
    if not email or not password:
        print("跳過 Email 發送：未設定環境變數")
        return

    # 建立信件內容
    content = top10_df.to_string(index=False)
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = Header('今日台股自動選股報表', 'utf-8')
    msg['From'] = email
    msg['To'] = email

    try:
        # Yahoo SMTP 固定設定
        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        print('Email 已成功送出')
    except Exception as e:
        print(f'Email 發送錯誤: {e}')

# 主程式邏輯
if __name__ == "__main__":
    # ... 你的抓取與計算邏輯 ...
    # results = [...] 
    
    if results:
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(by='總分', ascending=False)
        top10 = result_df.head(10)
        
        print("--- 今日選股前 10 名 ---")
        print(top10)
        
        # 執行發送
        send_email(top10)
        
        # 存檔 (供 GitHub Commit 使用)
        top10.to_csv('latest_stock_scan.csv', index=False, encoding='utf-8-sig')
