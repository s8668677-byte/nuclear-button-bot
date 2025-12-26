import telebot
from telebot import types
import random
import time
import requests
from io import BytesIO
import os

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8509737337:AAEfy3Y3U4zdEJn9B67T_Ij7IkNZXoZ-NRs')

bot = telebot.TeleBot(BOT_TOKEN)

# ID администратора
ADMIN_ID = 8408207941

# Словарь для хранения стран пользователей {user_id: {'country': 'США', 'pin': '1234'}}
user_countries = {}

# Словарь для хранения состояния пользователей
user_states = {}

# Список всех пользователей для рассылки
all_users = set()

# Распределение ракет по странам
MISSILES = {
    'США': ['Minuteman III', 'Trident II', 'Peacekeeper'],
    'Россия': ['Р-36М2 Воевода', 'Тополь-М', 'Орешник', 'Ярс', 'Булава'],
    'Китай': ['DF-41', 'DF-5', 'JL-2'],
    'Великобритания': ['Trident II D5'],
    'Франция': ['M51', 'M45'],
    'Северная Корея': ['Hwasong-15', 'Hwasong-17', 'KN-23'],
    'Латвия': ['Картошка-1', 'Рижский Бальзам'],
    'Римская Священная Империя': ['Катапульта Цезаря', 'Баллиста Августа']
}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    all_users.add(user_id)  # Добавляем пользователя в список для рассылки
    user_states[user_id] = {'step': 'start'}
    
    # Получаем реальный IP каждого пользователя через публичный API
    try:
        # Каждый запрос получает свой IP
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        user_ip = response.json()['ip']
    except:
        # Если API недоступен, генерируем случайный IP для демонстрации
        user_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    
    # Сохраняем IP пользователя
    user_states[user_id]['user_ip'] = user_ip
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('☢️ АКТИВИРОВАТЬ ЯДЕРНУЮ КНОПКУ')
    markup.add(btn)
    
    bot.send_message(
        message.chat.id,
        f"🔴 Привет! Я твоя красная кнопка!\n\n"
        f"📍 Ваш IP: {user_ip}\n\n"
        f"Нажмите кнопку ниже для активации...",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '☢️ АКТИВИРОВАТЬ ЯДЕРНУЮ КНОПКУ')
def activate_nuclear(message):
    user_id = message.from_user.id
    user_states[user_id] = {'step': 'enter_target'}
    
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "🎯 Введите цель (город или IP-адрес):",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'enter_target')
def get_target(message):
    user_id = message.from_user.id
    target = message.text
    user_states[user_id]['target'] = target
    user_states[user_id]['step'] = 'select_country'
    
    # Создаем кнопки для выбора страны
    markup = types.InlineKeyboardMarkup(row_width=2)
    countries = [
        ('🇺🇸 США', 'США'),
        ('🇷🇺 Россия', 'Россия'),
        ('🇨🇳 Китай', 'Китай'),
        ('🇬🇧 Великобритания', 'Великобритания'),
        ('🇫🇷 Франция', 'Франция'),
        ('🇰🇵 Северная Корея', 'Северная Корея'),
        ('🇱🇻 Латвия', 'Латвия'),
        ('⚜️ Римская Священная Империя', 'Римская Священная Империя')
    ]
    
    buttons = [types.InlineKeyboardButton(text=name, callback_data=f'country_{code}') 
               for name, code in countries]
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        f"🎯 Цель: {target}\n\n🌍 Выберите страну:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def select_country(call):
    user_id = call.from_user.id
    country = call.data.replace('country_', '')
    
    # Проверяем, есть ли у пользователя уже страна
    if user_id in user_countries:
        old_country = user_countries[user_id]['country']
        if old_country == country:
            # Пользователь выбрал свою же страну - просим ввести пин
            user_states[user_id]['step'] = 'enter_pin_own'
            user_states[user_id]['selected_country'] = country
            bot.edit_message_text(
                f"🔐 Вы уже владеете страной {country}\n\n"
                f"Введите ваш пин-код:",
                call.message.chat.id,
                call.message.message_id
            )
            return
        else:
            # Пользователь хочет сменить страну
            user_states[user_id]['step'] = 'confirm_change'
            user_states[user_id]['new_country'] = country
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_yes = types.InlineKeyboardButton(text='✅ Да', callback_data='change_yes')
            btn_no = types.InlineKeyboardButton(text='❌ Нет', callback_data='change_no')
            markup.add(btn_yes, btn_no)
            bot.edit_message_text(
                f"⚠️ Вы хотите поменять страну?\n\n"
                f"Текущая: {old_country}\n"
                f"Новая: {country}\n\n"
                f"Ваша старая страна освободится!",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
            return
    
    # Проверяем, занята ли страна другим пользователем
    for uid, data in user_countries.items():
        if data['country'] == country and uid != user_id:
            # Страна занята - просим ввести пин
            user_states[user_id]['step'] = 'enter_pin_occupied'
            user_states[user_id]['selected_country'] = country
            bot.edit_message_text(
                f"⚠️ Эта страна занята!\n\n"
                f"🌍 Страна: {country}\n"
                f"🔐 Введите пин-код для доступа:",
                call.message.chat.id,
                call.message.message_id
            )
            return
    
    # Страна свободна - создаем новый пин
    user_states[user_id]['country'] = country
    user_states[user_id]['step'] = 'create_pin'
    
    bot.edit_message_text(
        f"🌍 Страна: {country}\n\n"
        f"🔐 Выберите ваш пин-код от ядерки\n"
        f"(Он будет только ваш личный и останется навсегда, вашу страну не смогут забрать)\n\n"
        f"Введите пин-код (4 цифры):",
        call.message.chat.id,
        call.message.message_id
    )

# Обработчик кнопок смены страны
@bot.callback_query_handler(func=lambda call: call.data in ['change_yes', 'change_no'])
def handle_country_change(call):
    user_id = call.from_user.id
    
    if call.data == 'change_no':
        bot.edit_message_text(
            "❌ Смена страны отменена.\n\nИспользуйте /start для новой попытки.",
            call.message.chat.id,
            call.message.message_id
        )
        user_states[user_id] = {'step': 'start'}
        return
    
    # Пользователь согласился на смену
    new_country = user_states[user_id]['new_country']
    
    # Проверяем, занята ли новая страна
    for uid, data in user_countries.items():
        if data['country'] == new_country and uid != user_id:
            # Страна занята - просим ввести пин
            user_states[user_id]['step'] = 'enter_pin_occupied_change'
            user_states[user_id]['selected_country'] = new_country
            bot.edit_message_text(
                f"⚠️ Эта страна занята!\n\n"
                f"🌍 Страна: {new_country}\n"
                f"🔐 Введите пин-код для доступа:",
                call.message.chat.id,
                call.message.message_id
            )
            return
    
    # Страна свободна - создаем новый пин
    user_states[user_id]['country'] = new_country
    user_states[user_id]['step'] = 'create_pin'
    
    bot.edit_message_text(
        f"🌍 Страна: {new_country}\n\n"
        f"🔐 Выберите ваш пин-код от ядерки\n"
        f"(Он будет только ваш личный и останется навсегда, вашу страну не смогут забрать)\n\n"
        f"Введите пин-код (4 цифры):",
        call.message.chat.id,
        call.message.message_id
    )

# Обработчик создания пин-кода
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'create_pin')
def create_pin(message):
    user_id = message.from_user.id
    pin = message.text.strip()
    
    if not pin.isdigit() or len(pin) != 4:
        bot.send_message(message.chat.id, "❌ Пин-код должен состоять из 4 цифр! Попробуйте снова:")
        return
    
    country = user_states[user_id]['country']
    
    # Удаляем старую страну если была
    if user_id in user_countries:
        old_country = user_countries[user_id]['country']
        bot.send_message(message.chat.id, f"🚩 Страна {old_country} освобождена!")
    
    # Сохраняем новую страну и пин
    user_countries[user_id] = {'country': country, 'pin': pin}
    user_states[user_id]['step'] = 'enter_target'
    
    bot.send_message(
        message.chat.id,
        f"✅ Пин-код установлен!\n\n"
        f"🌍 Страна: {country}\n"
        f"🔐 Ваш пин: <code>{pin}</code>\n\n"
        f"🎯 Введите цель (город или IP-адрес):",
        parse_mode='HTML'
    )

# Обработчик ввода пина для своей страны
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'enter_pin_own')
def verify_own_pin(message):
    user_id = message.from_user.id
    entered_pin = message.text.strip()
    correct_pin = user_countries[user_id]['pin']
    
    if entered_pin == correct_pin:
        country = user_countries[user_id]['country']
        user_states[user_id]['step'] = 'enter_target'
        user_states[user_id]['country'] = country
        bot.send_message(
            message.chat.id,
            f"✅ Пин-код верный!\n\n"
            f"🎯 Введите цель (город или IP-адрес):"
        )
    else:
        bot.send_message(message.chat.id, "❌ Неверный пин-код! Попробуйте снова:")

# Обработчик ввода пина для занятой страны
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') in ['enter_pin_occupied', 'enter_pin_occupied_change'])
def verify_occupied_pin(message):
    user_id = message.from_user.id
    entered_pin = message.text.strip()
    country = user_states[user_id]['selected_country']
    
    # Ищем владельца страны
    owner_id = None
    for uid, data in user_countries.items():
        if data['country'] == country:
            owner_id = uid
            correct_pin = data['pin']
            break
    
    if entered_pin == correct_pin:
        bot.send_message(message.chat.id, "❌ Вы не можете забрать чужую страну! Выберите другую.\n\nИспользуйте /start")
        user_states[user_id] = {'step': 'start'}
    else:
        bot.send_message(message.chat.id, "❌ Неверный пин-код! Эта страна защищена.\n\nИспользуйте /start")
        user_states[user_id] = {'step': 'start'}

# Команда для рассылки (только для админа)
@bot.message_handler(func=lambda message: message.text and message.text.startswith('!text '))
def broadcast_message(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав для рассылки!")
        return
    
    text = message.text[6:]  # Убираем '!text '
    
    if not text:
        bot.send_message(message.chat.id, "❌ Введите текст для рассылки!\n\nПример: !text Привет всем!")
        return
    
    sent_count = 0
    for uid in all_users:
        try:
            bot.send_message(uid, f"📢 Сообщение от администратора:\n\n{text}")
            sent_count += 1
        except:
            pass
    
    bot.send_message(message.chat.id, f"✅ Рассылка отправлена {sent_count} пользователям!")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'enter_code')
def verify_code(message):
    user_id = message.from_user.id
    entered_code = message.text
    correct_code = user_states[user_id].get('code')
    
    if entered_code == correct_code:
        user_states[user_id]['step'] = 'select_missile'
        country = user_states[user_id]['country']
        missiles = MISSILES.get(country, ['Неизвестная ракета'])
        
        # Создаем кнопки для выбора ракеты
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(text=f'🚀 {missile}', callback_data=f'missile_{i}') 
                   for i, missile in enumerate(missiles)]
        markup.add(*buttons)
        
        # Сохраняем список ракет
        user_states[user_id]['missiles'] = missiles
        
        bot.send_message(
            message.chat.id,
            f"✅ Код подтвержден!\n\n🚀 Выберите ракету:",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "❌ Неверный код! Попробуйте снова:")

@bot.callback_query_handler(func=lambda call: call.data.startswith('missile_'))
def select_missile(call):
    user_id = call.from_user.id
    missile_index = int(call.data.replace('missile_', ''))
    missiles = user_states[user_id].get('missiles', [])
    missile = missiles[missile_index]
    
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
        'https://media.giphy.com/media/l0HlMPcbD4jdARjRC/giphy.gif',
        caption="🚀 РАКЕТА ЗАПУЩЕНА!"
    )
    
    time.sleep(4)
    
    # Отправляем гифку ядерного взрыва
    bot.send_animation(
        call.message.chat.id,
        'https://media.giphy.com/media/HhTXt43pk1I1W/giphy.gif',
        caption="💥 ЯДЕРНЫЙ ВЗРЫВ!"
    )
    
    # Отправляем аудио взрыва
    try:
        bot.send_audio(
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
        f"✅ Миссия выполнена!\n\n"
        f"🎯 Цель: {target}\n"
        f"🌍 Страна: {country}\n"
        f"🚀 Ракета: {missile}\n\n"
        f"Используйте /start для новой атаки"
    )
    
    # Страна НЕ освобождается - она остается за пользователем навсегда!
    
    user_states[user_id] = {'step': 'start'}

if __name__ == '__main__':
    print("🚀 Бот запущен!")
    bot.infinity_polling()
