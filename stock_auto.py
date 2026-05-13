import pandas as pd
        # 新聞分數
        news = news_score(stock)

        # 最終分數
        final_score = tech_score * 0.7 + news * 0.3

        # 建議開盤進場價
        entry_price = round(float(latest['Close']) * 0.985, 1)

        # 停損
        stop_loss = round(entry_price * 0.95, 1)

        results.append({
            '股票': stock,
            '收盤價': round(float(latest['Close']), 1),
            '技術分數': tech_score,
            '新聞分數': news,
            '總分': round(final_score, 1),
            '建議進場價': entry_price,
            '停損價': stop_loss
        })

    except Exception as e:
        print(stock, e)

# ==========================
# 排序
# ==========================

result_df = pd.DataFrame(results)

result_df = result_df.sort_values(
    by='總分',
    ascending=False
)

# 前10名

top10 = result_df.head(10)

print(top10)

# ==========================
# Email 發送
# ==========================

content = top10.to_string(index=False)

msg = MIMEText(content)
msg['Subject'] = '今日台股自動選股'
msg['From'] = 'a26805848@yahoo.com.tw'
msg['To'] = 'a26805848@yahoo.com.tw'

server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
server.starttls()

server.login(
    'a26805848@yahoo.com.tw,
    'maInt8aiN-@852'
)

server.send_message(msg)
server.quit()

print('Email 已送出')
