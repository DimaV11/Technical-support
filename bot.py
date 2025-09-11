import telebot
from telebot import types
from config import API_TOKEN, ADMIN_PASSWORD, ADMIN_USERNAME
from database import create_db, register_user, authenticate_user, save_request, get_requests
from faq import FAQ
    
bot = telebot.TeleBot(API_TOKEN)
user_auth_status = {}

@bot.message_handler(commands=['start'])
def start(message):
    """Обрабатывает команду /start."""
    chat_id = message.chat.id
    user_auth_status[chat_id] = None 

    show_auth_menu(chat_id)

def show_auth_menu(chat_id):
    """Отображает меню для выбора аутентификации или регистрации."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(types.KeyboardButton('🔑 Регистрация'))
    markup.add(types.KeyboardButton('✅ Вход'))
    markup.add(types.KeyboardButton('🛡️ Вход как администратор'))
    bot.send_message(chat_id, "👋 Привет! Я ваш ассистент. Пожалуйста, выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🛡️ Вход как администратор')
def admin_login_request(message):
    """Запрашивает имя пользователя для входа администратора."""
    chat_id = message.chat.id
    bot.send_message(chat_id, "👮 Введите имя пользователя администратора:")
    bot.register_next_step_handler(message, process_admin_username)

def process_admin_username(message):
    """Обрабатывает введенное имя пользователя администратора."""
    chat_id = message.chat.id
    username_entered = message.text.strip()
    bot.send_message(chat_id, "🔒 Введите пароль администратора:")
    bot.register_next_step_handler(message, lambda msg: finalize_admin_login(msg, username_entered))

def finalize_admin_login(message, entered_username):
    """Завершает процесс входа администратора, проверяя логин и пароль."""
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
    """Отображает главное меню для авторизованного администратора."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(types.KeyboardButton('❓ Часто задаваемые вопросы'))
    markup.add(types.KeyboardButton('✉️ Связаться с поддержкой'))
    markup.add(types.KeyboardButton('📋 Просмотреть запросы'))
    markup.add(types.KeyboardButton('🚪 Выйти из режима администратора'))
    bot.send_message(chat_id, "🌟 Меню администратора. Чем займемся?", reply_markup=markup)

def show_user_main_menu(chat_id):
    """Отображает главное меню для обычного пользователя."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(types.KeyboardButton('❓ Часто задаваемые вопросы'))
    markup.add(types.KeyboardButton('✉️ Связаться с поддержкой'))
    bot.send_message(chat_id, "🌟 Меню. Чем могу помочь?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '✅ Вход')
def user_login_request(message):
    """Запрашивает логин для входа обычного пользователя."""
    chat_id = message.chat.id
    bot.send_message(chat_id, "👤 Введите ваш логин (e-mail):")
    bot.register_next_step_handler(message, process_user_login)

def process_user_login(message):
    """Обрабатывает введенный логин пользователя."""
    chat_id = message.chat.id
    login = message.text.strip()
    bot.send_message(chat_id, "🔑 Введите ваш пароль:")
    bot.register_next_step_handler(message, lambda msg: finalize_user_login(msg, login))

def finalize_user_login(message, entered_login):
    """Завершает процесс входа обычного пользователя."""
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
    """Запрашивает данные для регистрации нового пользователя."""
    chat_id = message.chat.id
    bot.send_message(chat_id, "📝 Введите ваш user для регистрации:")
    bot.register_next_step_handler(message, process_user_registration_email)

def process_user_registration_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    bot.send_message(chat_id, "🔒 Введите пароль для регистрации:")
    bot.register_next_step_handler(message, lambda msg: process_user_registration_password(msg, email))

def process_user_registration_password(message, email):
    chat_id = message.chat.id
    password = message.text.strip()
    if register_user(chat_id, email, password): 
        user_auth_status[chat_id] = 'user'
        bot.reply_to(message, "🎉 Вы успешно зарегистрировались! Добро пожаловать!")
        show_user_main_menu(chat_id)
    else:
        bot.reply_to(message, "😔 Ошибка регистрации. Возможно, такой e-mail уже используется. Попробуйте снова.")
        start(message)

@bot.message_handler(func=lambda message: True)
def handle_main_menu_messages(message):
    """Обрабатывает сообщения из главного меню."""
    chat_id = message.chat.id
    user_message = message.text.strip()

    current_auth_status = user_auth_status.get(chat_id)

    if current_auth_status:
        if user_message == '❓ Часто задаваемые вопросы':
            bot.send_message(chat_id, "📚 Выберите тему из списка:")
            # Отображаем кнопки с темами из FAQ
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            for theme in FAQ:
                markup.add(types.KeyboardButton(theme))
            bot.send_message(chat_id, "❓ Пожалуйста, введите ваш вопрос из списка ниже:", reply_markup=markup)

        elif user_message in FAQ:
            bot.reply_to(message, f"📖 Ответ на ваш вопрос:\n\n{FAQ[user_message]}")

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
                                f"🏷️ Department: `{req[3]}`\n" \
                                f"📅 Date: `{req[4]}`\n" \
                                f"--------------------\n"
                bot.send_message(chat_id, response, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "🌟 Запросов пока нет.")

        elif user_message == '🚪 Выйти из режима администратора' and current_auth_status == 'admin':
            user_auth_status[chat_id] = None
            bot.reply_to(message, "👋 Вы успешно вышли из режима администратора.")
            start(message) 

        else:
            bot.reply_to(message, "🤔 Извините, я не понимаю этот запрос. Ваш вопрос будет сохранен для дальнейшей обработки.")
            save_request(chat_id, user_message, "general")
    else:
        bot.reply_to(message, "❌ Пожалуйста, сначала авторизуйтесь или зарегистрируйтесь, используя меню ниже.")
        start(message) 

if __name__ == '__main__':
    create_db() 
    print("Бот запущен...")
    bot.polling()
