import telebot
from telebot import types
from config import API_TOKEN, ADMIN_PASSWORD, ADMIN_USERNAME
from database import create_db, register_user, authenticate_user, save_request, get_requests, get_all_faq_items, delete_user

bot = telebot.TeleBot(API_TOKEN)

user_auth_status = {}

try:
    FAQ = get_all_faq_items()
    if not FAQ:
        print("FAQ пуст в базе данных. Пожалуйста, убедитесь, что load_initial_faq_data() была вызвана в database.py.")
except Exception as e:
    print(f"Ошибка при загрузке FAQ из базы данных: {e}")
    FAQ = {}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_auth_status[chat_id] = None
    show_auth_menu(chat_id)

def show_auth_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(types.KeyboardButton('🔑 Регистрация'))
    markup.add(types.KeyboardButton('✅ Вход'))
    markup.add(types.KeyboardButton('🛡 Вход как администратор'))
    markup.add(types.KeyboardButton('❌ Удалить аккаунт'))
    bot.send_message(chat_id, "👋 Привет! Я ваш ассистент. Пожалуйста, выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '❌ Удалить аккаунт')
def delete_account_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔒 Введите ваш логин для удаления аккаунта:")
    bot.register_next_step_handler(message, process_delete_username)

def process_delete_username(message):
    chat_id = message.chat.id
    entered_login = message.text.strip()
    bot.send_message(chat_id, "🔑 Введите ваш пароль для удаления аккаунта:")
    bot.register_next_step_handler(message, lambda msg: finalize_delete_account(msg, entered_login))

def finalize_delete_account(message, entered_login):
    chat_id = message.chat.id
    password = message.text.strip()
    user_data = authenticate_user(entered_login, password)  
    if user_data:
        delete_user(entered_login)
        bot.reply_to(message, "🗑 Ваш аккаунт успешно удалён.")
        start(message)  
    else:
        bot.reply_to(message, "❌ Неверный логин или пароль. Удаление аккаунта невозможно.")
        start(message)

@bot.message_handler(func=lambda message: message.text == '🛡 Вход как администратор')
def admin_login_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "👮 Введите имя пользователя администратора:")
    bot.register_next_step_handler(message, process_admin_username)

def process_admin_username(message):
    chat_id = message.chat.id
    username_entered = message.text.strip()
    bot.send_message(chat_id, "🔒 Введите пароль администратора:")
    bot.register_next_step_handler(message, lambda msg: finalize_admin_login(msg, username_entered))

def finalize_admin_login(message, entered_username):
    chat_id = message.chat.id
    password_entered = message.text.strip()

    if entered_username == ADMIN_USERNAME and password_entered == ADMIN_PASSWORD:
        user_auth_status[chat_id] = 'admin'
        bot.reply_to(message, "✨ Добро пожаловать, администратор! Вы успешно вошли.")
        show_admin_main_menu(chat_id)
    else:
        bot.reply_to(message, "❌ Неверное имя пользователя или пароль. Попробуйте снова.")
        start(message)

def show_admin_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(types.KeyboardButton('❓ Часто задаваемые вопросы'))
    markup.add(types.KeyboardButton('✉️ Связаться с поддержкой'))
    markup.add(types.KeyboardButton('📋 Просмотреть запросы'))
    markup.add(types.KeyboardButton('🚪 Выйти из режима администратора'))
    bot.send_message(chat_id, "🌟 Меню администратора. Чем займемся?", reply_markup=markup)

def show_user_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(types.KeyboardButton('❓ Часто задаваемые вопросы'))
    markup.add(types.KeyboardButton('✉️ Связаться с поддержкой'))
    markup.add(types.KeyboardButton('🚪 Выйти из аккаунта'))
    bot.send_message(chat_id, "🌟 Меню. Чем могу помочь?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '✅ Вход')
def user_login_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "👤 Введите ваш логин")
    bot.register_next_step_handler(message, process_user_login)

def process_user_login(message):
    chat_id = message.chat.id
    login = message.text.strip()
    bot.send_message(chat_id, "🔑 Введите ваш пароль:")
    bot.register_next_step_handler(message, lambda msg: finalize_user_login(msg, login))

def finalize_user_login(message, entered_login):
    chat_id = message.chat.id
    password = message.text.strip()
    user_data = authenticate_user(entered_login, password)
    if user_data:
        user_auth_status[chat_id] = 'user'
        bot.reply_to(message, f"🥳 Добро пожаловать, {entered_login}! Вы успешно вошли.")
        show_user_main_menu(chat_id)
    else:
        bot.reply_to(message, "❌ Неверный логин или пароль. Попробуйте снова.")
        start(message)

@bot.message_handler(func=lambda message: message.text == '🔑 Регистрация')
def register_user_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "📝 Введите ваш логин для регистрации:")
    bot.register_next_step_handler(message, process_user_registration_email)

def process_user_registration_email(message):
    chat_id = message.chat.id
    email = message.text.strip()

    if not email:
        bot.send_message(chat_id, "❌ Логин не должен быть пустым. Введите ваш e-mail:")
        bot.register_next_step_handler(message, process_user_registration_email)
        return

    if len(email) < 3 or len(email) > 20:
        bot.send_message(chat_id, "🚫 Логин должен быть от 3 до 20 символов. Пожалуйста, введите корректный логин:")
        bot.register_next_step_handler(message, process_user_registration_email)
        return

    bot.send_message(chat_id, "🔒 Введите пароль для регистрации:")
    bot.register_next_step_handler(message, lambda msg: process_user_registration_password(msg, email))

def process_user_registration_password(message, email):
    chat_id = message.chat.id
    password = message.text.strip()

    if len(password) < 6 or len(password) > 24:
        bot.send_message(chat_id, "🚫 Пароль должен быть от 6 до 24 символов. Пожалуйста, введите корректный пароль:")
        bot.register_next_step_handler(message, lambda msg: process_user_registration_password(msg, email))
        return

    if register_user(chat_id, email, password): 
        user_auth_status[chat_id] = True
        bot.reply_to(message, "🎉 Вы успешно зарегистрировались! Добро пожаловать!")
        show_user_main_menu(chat_id)
    else:
        bot.reply_to(message, "😔 Ошибка регистрации. Возможно, такой логин уже используется или вы уже зарегистрировались. Попробуйте снова.")
        start(message)


MAIN_MENU_BUTTON = "🔙 В главное меню"
FAQ_KEYBOARD_MARKUP = None

def create_faq_markup():
    global FAQ_KEYBOARD_MARKUP
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    if FAQ:
        for theme in FAQ:
            markup.add(types.KeyboardButton(theme))
        markup.add(types.KeyboardButton(MAIN_MENU_BUTTON)) 
        FAQ_KEYBOARD_MARKUP = markup 
    return FAQ_KEYBOARD_MARKUP

@bot.message_handler(func=lambda message: True)
def handle_main_menu_messages(message):
    chat_id = message.chat.id
    user_message = message.text.strip()

    current_auth_status = user_auth_status.get(chat_id)

    if current_auth_status:
        if user_message == '❓ Часто задаваемые вопросы':
            bot.send_message(chat_id, "📚 Выберите тему из списка:")
            markup = create_faq_markup() 
            if markup:
                bot.send_message(chat_id, "❓ Пожалуйста, введите ваш вопрос из списка ниже:", reply_markup=markup)
            else:
                bot.send_message(chat_id, "😔 Извините, раздел FAQ пока пуст.")

        elif user_message in FAQ:
            bot.reply_to(message, f"📖 Ответ на ваш вопрос:\n\n{FAQ[user_message]}")

        elif user_message == MAIN_MENU_BUTTON:
            bot.send_message(chat_id, "Возвращаемся в главное меню.")
            if current_auth_status == 'admin':
                show_admin_main_menu(chat_id)
            else:
                show_user_main_menu(chat_id)

        elif user_message == '✉️ Связаться с поддержкой':
            bot.send_message(chat_id, "📝 Пожалуйста, оставьте ваше сообщение, и мы свяжемся с вами.")
            save_request(chat_id, user_message, "support")

        elif user_message == '📋 Просмотреть запросы' and current_auth_status == 'admin':
            requests = get_requests()
            if requests:
                response = "📋 **Список всех запросов:**\n\n"
                for req in requests:
                    response += f"✨ ID: `{req[0]}`\n" \
                                f"👤 User ID: `{req[1]}`\n" \
                                f"📝 Message: `{req[2]}`\n" \
                                f"🏷 Department: `{req[3]}`\n" \
                                f"📅 Date: `{req[4]}`\n" \
                                f"--------------------\n"
                bot.send_message(chat_id, response, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "🌟 Запросов пока нет.")

        elif user_message == '🚪 Выйти из режима администратора' and current_auth_status == 'admin':
            user_auth_status[chat_id] = None
            bot.reply_to(message, "👋 Вы успешно вышли из режима администратора.")
            start(message)

        elif user_message == '🚪 Выйти из аккаунта':
            user_auth_status[chat_id] = None
            bot.reply_to(message, "👋 Вы успешно вышли из вашего аккаунта.")
            start(message)

        else:
            bot.reply_to(message, "🤔 Извините, я не понимаю этот запрос. Ваш вопрос будет сохранен для дальнейшей обработки.")
            save_request(chat_id, user_message, "user")
    else:
        bot.reply_to(message, "❌ Пожалуйста, сначала авторизуйтесь или зарегистрируйтесь, используя меню ниже.")
        start(message)

if __name__ == '__main__':
    

    print("🚀 Бот запущен...")
    bot.polling()
