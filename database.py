import sqlite3
from datetime import datetime
import hashlib

DB_FILE = 'support_requests.db'

def create_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            department TEXT NOT NULL,
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(chat_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faq_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE NOT NULL,
            answer TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(chat_id, email, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    hashed_password = _hash_password(password)
    try:
        cursor.execute("INSERT INTO users (chat_id, email, password) VALUES (?, ?, ?)", 
                       (chat_id, email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        return False
    finally:
        conn.close()


def authenticate_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    hashed_password = _hash_password(password)
    cursor.execute("SELECT chat_id FROM users WHERE email = ? AND password = ?", (email, hashed_password))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def delete_user(login):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE email=?", (login,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при удалении пользователя: {e}")
    finally:
        conn.close()


def save_request(user_id, message, department):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO requests (user_id, message, department) VALUES (?, ?, ?)",
                       (user_id, message, department))
        conn.commit()
    except Exception as e:
        print(f"Ошибка сохранения запроса: {e}")
    finally:
        conn.close()

def get_requests():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, message, department, request_date FROM requests")
    requests = cursor.fetchall()
    conn.close()
    return requests

def add_faq_item(question, answer):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO faq_items (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
        print(f"FAQ: Добавлен вопрос: '{question}'")
        return True
    except sqlite3.IntegrityError:
        print(f"FAQ: Вопрос '{question}' уже существует.")
        return False
    finally:
        conn.close()

def get_all_faq_items():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM faq_items")
    rows = cursor.fetchall()
    conn.close()
    faq_dict = {row[0]: row[1] for row in rows}
    return faq_dict

def load_initial_faq_data():
    existing_faq = get_all_faq_items()
    if not existing_faq:
        initial_faq = {
            "Как оформить заказ?": "Для оформления заказа выберите интересующий вас товар и нажмите кнопку 'Добавить в корзину', затем перейдите в корзину и следуйте инструкциям для завершения покупки.",
            "Как узнать статус моего заказа?": "Вы можете узнать статус вашего заказа, войдя в свой аккаунт на нашем сайте и перейдя в раздел 'Мои заказы'.",
            "Как отменить заказ?": "Если вы хотите отменить заказ, пожалуйста, свяжитесь с нашей службой поддержки как можно скорее.",
            "Что делать, если товар пришел поврежденным?": "При получении поврежденного товара, пожалуйста, свяжитесь с нашей службой поддержки и предоставьте фотографии повреждений.",
            "Как связаться с вашей технической поддержкой?": "Вы можете связаться с нашей технической поддержкой через телефон на нашем сайте или написать нам в чат-бота.",
            "Как узнать информацию о доставке?": "Информацию о доставке вы можете найти на странице оформления заказа на нашем сайте."
        }
        print("Начальная загрузка FAQ...")
        for question, answer in initial_faq.items():
            add_faq_item(question, answer)
        print("Начальная загрузка FAQ завершена.")
    else:
        print("FAQ данные уже существуют в базе данных.")

if __name__ == '__main__':
    load_initial_faq_data()
    print("База данных и FAQ подготовлены.")
