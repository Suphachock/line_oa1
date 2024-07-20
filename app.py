from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage
import pymysql
import re

app = Flask(__name__)

# -------------- กำหนด Line OA --------------
line_bot_api = LineBotApi(
    '9rppx6uBQhON/yenS+HHhysjcAC5n/+4ZTpZhAeTCzfCvkd+Layq96PXKCIF1GnT4V0VZLGjc/wctE6O7GeWFZocuiabrc/fYw6cP7K6Y1FxzOjKHURWgLZ42hSHD7OtBeaQsfrcdjH/5Z9cApWEXAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('fa78d0cc7c3225fcd3cbfb9003b45f88')

# -------- เชื่อมต่อฐานข้อมูล phpmyadmin --------
def connect_db():
    return pymysql.connect(
        host='127.0.0.1',
        # host="host.docker.internal",
        user='root',
        password='',
        db='employee',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=3
    )

# ---------------- หน้า Index ----------------
@app.route("/")
def index():
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM emp_data LIMIT 10"  # ตัวอย่างการดึงข้อมูลพนักงาน 10 คน
            cursor.execute(sql)
            result = cursor.fetchall()
            employees = "<ul>"
            for emp in result:
                employees += f"<li>{emp['emp_name']} (ID: {emp['emp_id']})</li>"
            employees += "</ul>"
        return f"<h1>Employee List</h1>{employees}"
    except Exception as e:
        return f"Error occurred: {e}", 500
    finally:
        connection.close()

# ------------------------------------------
@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    print("Request Body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Abort.")
        abort(400)

    print("Request handled successfully.")
    return 'OK', 200

# -------- ลงทะเบียนรหัสพนักงาน --------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text  # ดึงข้อความ
    user_id = event.source.user_id  # ดึง u_id ของ line user
    if '/รหัสพนักงาน' in text:
        match = re.match(r'/รหัสพนักงาน:(\d+)', text)
        if match:
            emp_id = match.group(1)
            # print(f"Extracted Employee ID: {emp_id}")
            connection = connect_db()
            try:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM emp_data WHERE emp_id = %s"
                    cursor.execute(sql, (emp_id,))
                    result = cursor.fetchone()
                    if result:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text=f"ชื่อพนักงาน: {result['emp_name']}")
                        )
                    else:
                        line_bot_api.reply_message(
                            event.reply_token, TextSendMessage(text='Employee ID not found'))
                        print("Reply sent: Employee ID not found")
            except Exception as e:
                print("Error occurred:", e)
            finally:
                connection.close()
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text='Invalid format. Please use "/รหัสพนักงาน:1234".'))
            print("Reply sent: Invalid format")

# -------- เก็บ user_id หลังจาก Add Friend Line OA --------
@handler.add(FollowEvent)
def handle_follow(event):
    try:
        user_id = event.source.user_id
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        connection = connect_db()
        try:
            with connection.cursor() as cursor:
                # Check if the user is already registered
                sql = "SELECT * FROM emp_line_id WHERE emp_line_id = %s"
                cursor.execute(sql, (user_id,))
                user = cursor.fetchone()

                if not user:
                    # Insert new user into the database
                    sql = "INSERT INTO emp_line_id (emp_line_id, emp_line_name) VALUES (%s, %s)"
                    cursor.execute(sql, (user_id, display_name))
                    connection.commit()
                    print(f"Stored new user: {user_id}")

                    # Send a welcome message
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f'สวัสดี! {display_name}')
                    )
                else:
                    print(f"User {user_id} is already registered.")
        finally:
            connection.close()
    except Exception as e:
        print("Error occurred:", e)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
