import os
import smtplib
import pandas as pd
import pandas_ta as ta  # 確保套件正確載入
from email.mime.text import MIMEText
from email.header import Header

def send_yahoo_email(df):
    email_user = os.environ.get('YAHOO_EMAIL')
    email_password = os.environ.get('YAHOO_PASSWORD')
    
    if not email_user or not email_password:
        print("未偵測到環境變數，跳過 Email 發送")
        return

    # 將結果轉為表格文字
    content = "今日選股結果：\n\n" + df.to_string(index=False)
    
    # 建立 Email 內容，務必指定 utf-8
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = Header('台股自動選股掃描報告', 'utf-8')
    msg['From'] = email_user
    msg['To'] = email_user

    try:
        # Yahoo SMTP 固定設定
        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        print('Email 已成功送出至 Yahoo 信箱')
    except Exception as e:
        print(f'Email 發送錯誤: {e}')

if __name__ == "__main__":
    print("正在執行選股邏輯...")
    
    # --- 這裡放入你的選股邏輯範例 ---
    # 範例資料結構
    results = [
        {'股票代號': '2330', '名稱': '台積電', '總分': 95},
        {'股票代號': '2317', '名稱': '鴻海', '總分': 88}
    ]
    # ----------------------------
    
    if results:
        df_final = pd.DataFrame(results).sort_values(by='總分', ascending=False)
        
        # 1. 印出結果
        print(df_final)
        
        # 2. 寄送 Email
        send_yahoo_email(df_final)
        
        # 3. 儲存 CSV (供 GitHub 存檔)
        df_final.to_csv('stock_report.csv', index=False, encoding='utf-8-sig')
    else:
        print("今日無符合篩選條件之股票")
