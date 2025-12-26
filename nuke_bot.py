import telebot
from telebot import types
import random
import time
import requests

# ВСТАВЬТЕ СЮДА ВАШ ТОКЕН ОТ @BotFather
import os
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

bot = telebot.TeleBot(BOT_TOKEN)

# ID администратора
ADMIN_ID = 8408207941

# Словарь для хранения стран пользователей {user_id: {'country': 'США', 'pin': '1234', 'owner_id': 123}}
user_countries = {}

# Словарь для хранения состояния пользователей
user_states = {}

# Список всех пользователей для рассылки
all_users = set()

# Распределение ракет по странам
MISSILES = {
    'США': ['Minuteman III', 'Trident II D5', 'Peacekeeper MX', 'Titan II', 'Atlas F', 'LGM-118A', 'UGM-133A', 'Polaris A3'],
    'Россия': ['Р-36М2 Воевода', 'Тополь-М', 'Орешник', 'Ярс РС-24', 'Булава', 'Сармат РС-28', 'Авангард', 'Кинжал', 'Циркон', 'Искандер-М', 'Калибр'],
    'Китай': ['DF-41', 'DF-5B', 'DF-31AG', 'JL-2', 'DF-17', 'DF-26', 'DF-21D', 'JL-3', 'DF-4'],
    'Великобритания': ['Trident II D5', 'Polaris A3', 'Chevaline', 'Blue Streak'],
    'Франция': ['M51', 'M45', 'M4', 'ASMP-A', 'S3', 'Pluton'],
    'Северная Корея': ['Hwasong-15', 'Hwasong-17', 'Hwasong-14', 'KN-23', 'Pukkuksong-2', 'Taepodong-2', 'Musudan'],
    'Латвия': ['Картошка-1', 'Рижский Бальзам', 'Шпроты-М', 'Бальзам Черный', 'Килька в томате'],
    'Римская Священная Империя': ['Катапульта Цезаря', 'Баллиста Августа', 'Требушет Константина', 'Онагр Траяна']
}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    all_users.add(user_id)
    user_states[user_id] = {'step': 'start'}
    
    # Получаем реальный IP каждого пользователя
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        user_ip = response.json()['ip']
    except:
        user_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔴 АКТИВИРОВАТЬ ЯДЕРНУЮ КНОПКУ'))
    
    bot.send_message(
        message.chat.id,
        f"🔴 Привет! Я твоя красная кнопка!\n\n"
        f"📍 Ваш IP: {user_ip}\n\n"
        f"Нажмите кнопку ниже для активации ядерного арсенала.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '🔴 АКТИВИРОВАТЬ ЯДЕРНУЮ КНОПКУ')
def activate_button(message):
    user_id = message.from_user.id
    user_states[user_id] = {'step': 'enter_target'}
    
    bot.send_message(
        message.chat.id,
        "🎯 Введите цель (город или IP-адрес):"
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'enter_target')
def enter_target(message):
    user_id = message.from_user.id
    target = message.text
    user_states[user_id]['target'] = target
    user_states[user_id]['step'] = 'select_country'
    
    # Проверяем есть ли у пользователя уже страна
    user_country_data = user_countries.get(user_id)
    
    if user_country_data:
        # У пользователя уже есть страна
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('✅ Да', callback_data='change_country_yes'),
            types.InlineKeyboardButton('❌ Нет', callback_data='change_country_no')
        )
        bot.send_message(
            message.chat.id,
            f"У вас уже есть страна: {user_country_data['country']}\n"
            f"Ваш пин-код: {user_country_data['pin']}\n\n"
            f"Вы хотите поменять страну?",
            reply_markup=markup
        )
    else:
        # Показываем выбор страны
        show_country_selection(message.chat.id, user_id)

def show_country_selection(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    countries = list(MISSILES.keys())
    
    buttons = []
    for country in countries:
        # Проверяем занята ли страна
        is_taken = any(data['country'] == country for uid, data in user_countries.items() if uid != user_id)
        
        if is_taken:
            buttons.append(types.InlineKeyboardButton(f"🔒 {country}", callback_data=f"country_{country}"))
        else:
            buttons.append(types.InlineKeyboardButton(f"🌍 {country}", callback_data=f"country_{country}"))
    
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "🌍 Выберите вашу страну:\n\n"
        "🌍 - свободна\n"
        "🔒 - занята (требуется пин-код)",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'change_country_yes')
def change_country_yes(call):
    user_id = call.from_user.id
    
    # Освобождаем старую страну
    if user_id in user_countries:
        del user_countries[user_id]
    
    bot.edit_message_text(
        "Ваша страна освобождена. Выберите новую:",
        call.message.chat.id,
        call.message.message_id
    )
    
    show_country_selection(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == 'change_country_no')
def change_country_no(call):
    user_id = call.from_user.id
    country = user_countries[user_id]['country']
    
    user_states[user_id]['country'] = country
    user_states[user_id]['step'] = 'enter_code'
    
    bot.edit_message_text(
        f"Отлично! Используем {country}\n\n"
        f"🔐 Введите код активации:",
        call.message.chat.id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def select_country(call):
    user_id = call.from_user.id
    country = call.data.replace('country_', '')
    
    # Проверяем занята ли страна другим пользователем
    country_owner = None
    for uid, data in user_countries.items():
        if data['country'] == country and uid != user_id:
            country_owner = uid
            break
    
    if country_owner:
        # Страна занята - просим пин
        user_states[user_id]['pending_country'] = country
        user_states[user_id]['step'] = 'enter_pin_to_take'
        
        bot.edit_message_text(
            f"🔒 Страна {country} занята!\n\n"
            f"Введите пин-код от этой страны (если знаете):",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        # Страна свободна - создаем пин
        pin = str(random.randint(1000, 9999))
        user_countries[user_id] = {
            'country': country,
            'pin': pin,
            'owner_id': user_id
        }
        user_states[user_id]['country'] = country
        user_states[user_id]['step'] = 'enter_code'
        
        bot.edit_message_text(
            f"✅ Вы выбрали: {country}\n\n"
            f"🔐 Ваш пин-код от ядерки: {pin}\n"
            f"(Он будет только ваш личный и останется навсегда, вашу страну не смогут забрать)\n\n"
            f"Теперь введите код активации:",
            call.message.chat.id,
            call.message.message_id
        )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'enter_pin_to_take')
def enter_pin_to_take(message):
    user_id = message.from_user.id
    entered_pin = message.text.strip()
    pending_country = user_states[user_id].get('pending_country')
    
    # Находим владельца страны
    country_owner_id = None
    correct_pin = None
    for uid, data in user_countries.items():
        if data['country'] == pending_country:
            country_owner_id = uid
            correct_pin = data['pin']
            break
    
    if entered_pin == correct_pin:
        bot.send_message(
            message.chat.id,
            f"❌ Пин-код правильный, но вы НЕ МОЖЕТЕ забрать чужую страну!\n"
            f"Эта страна навсегда принадлежит другому пользователю.\n\n"
            f"Выберите другую страну:"
        )
        show_country_selection(message.chat.id, user_id)
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Неправильный пин-код!\n\n"
            f"Выберите другую страну:"
        )
        show_country_selection(message.chat.id, user_id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'enter_code')
def enter_code(message):
    user_id = message.from_user.id
    code = message.text
    
    # Любой код правильный
    country = user_states[user_id]['country']
    user_states[user_id]['step'] = 'select_missile'
    
    bot.send_message(
        message.chat.id,
        f"✅ Код принят!\n\n"
        f"🚀 Выберите ракету из арсенала {country}:"
    )
    
    # Показываем ракеты для выбранной страны
    markup = types.InlineKeyboardMarkup(row_width=1)
    missiles = MISSILES.get(country, [])
    
    for missile in missiles:
        markup.add(types.InlineKeyboardButton(f"🚀 {missile}", callback_data=f"missile_{missile}"))
    
    bot.send_message(message.chat.id, "Выберите ракету:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('missile_'))
def select_missile(call):
    user_id = call.from_user.id
    missile = call.data.replace('missile_', '')
    
    user_states[user_id]['missile'] = missile
    
    bot.edit_message_text(
        f"🚀 Ракета выбрана: {missile}\n\n"
        f"⏱ Запуск через 10 секунд...",
        call.message.chat.id,
        call.message.message_id
    )
    
    # Обратный отсчет
    for i in range(10, 0, -1):
        time.sleep(1)
        try:
            bot.edit_message_text(
                f"🚀 Ракета: {missile}\n\n"
                f"⏱ Запуск через {i} секунд...",
                call.message.chat.id,
                call.message.message_id
            )
        except:
            pass
    
    # Отправляем гифку полета ракеты
    bot.send_animation(
        call.message.chat.id,
        'https://media1.tenor.com/m/r6oUJB910uMAAAAd/かみ太.gif',
        caption="🚀 РАКЕТА ЗАПУЩЕНА!"
    )
    
    time.sleep(4)
    
    # Отправляем гифку ядерного взрыва
    bot.send_animation(
        call.message.chat.id,
        'https://media.giphy.com/media/HhTXt43pk1I1W/giphy.gif',
        caption="💥 ЯДЕРНЫЙ ВЗРЫВ!"
    )
    
    # Отправляем голосовое сообщение со звуком взрыва
    try:
        bot.send_voice(
            call.message.chat.id,
            'https://www.soundjay.com/misc/sounds/explosion-01.mp3'
        )
    except:
        pass
    
    # Очищаем состояние
    target = user_states[user_id].get('target', 'Неизвестно')
    country = user_states[user_id].get('country', 'Неизвестно')
    
    bot.send_message(
        call.message.chat.id,
        f"✅ Миссия завершена!\n\n"
        f"🎯 Цель: {target}\n"
        f"🌍 Страна: {country}\n"
        f"🚀 Ракета: {missile}\n\n"
        f"Нажмите /start для новой миссии"
    )
    
    user_states[user_id] = {'step': 'start'}

# Команда рассылки для админа
@bot.message_handler(func=lambda message: message.text.startswith('!text ') and message.from_user.id == ADMIN_ID)
def broadcast_message(message):
    text_to_send = message.text.replace('!text ', '', 1)
    
    success_count = 0
    fail_count = 0
    
    for user_id in all_users:
        try:
            bot.send_message(user_id, f"📢 Сообщение от администратора:\n\n{text_to_send}")
            success_count += 1
        except:
            fail_count += 1
    
    bot.send_message(
        message.chat.id,
        f"✅ Рассылка завершена!\n\n"
        f"Отправлено: {success_count}\n"
        f"Ошибок: {fail_count}"
    )

print("🚀 Бот запущен!")
bot.infinity_polling()
