def send_email(content):

    user = os.environ.get("YAHOO_EMAIL")
    pwd = os.environ.get("YAHOO_PASSWORD")

    if not user or not pwd:
        print("缺 Email")
        return

    try:
        server = smtplib.SMTP("smtp.mail.yahoo.com", 587, timeout=30)
        
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(user, pwd)

        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = Header("📱 台股量化3.2報告", "utf-8")
        msg["From"] = user
        msg["To"] = user

        server.send_message(msg)

        server.quit()

        print("Email 已寄出")

    except Exception as e:
        print(f"Email 失敗: {e}")

        try:
            server.quit()
        except:
            pass
