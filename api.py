import pymysql
import requests

# MySQL database connection
def get_data_from_db():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="employee"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, emp_line_id,emp_line_name FROM emp_line_id")
    result = cursor.fetchall()
    conn.close()
    return result

# Function to send Line notification
def send_line_notification(user_id, message):
    access_token = '9rppx6uBQhON/yenS+HHhysjcAC5n/+4ZTpZhAeTCzfCvkd+Layq96PXKCIF1GnT4V0VZLGjc/wctE6O7GeWFZocuiabrc/fYw6cP7K6Y1FxzOjKHURWgLZ42hSHD7OtBeaQsfrcdjH/5Z9cApWEXAdB04t89/1O/w1cDnyilFU='
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'to': user_id,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)
    return response.status_code

# Main function to get data and send notifications
def main():
    data = get_data_from_db()
    for emp_id, emp_line_id,emp_line_name in data:
        message = f"Data for employee {emp_id}: Name :{emp_line_name}"
        status = send_line_notification(emp_line_id, message)
        if status == 200:
            print(f"Message sent to {emp_line_name}")
        else:
            print(f"Failed to send message to {emp_line_name}")

if __name__ == "__main__":
    main()
