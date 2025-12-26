import telebot
from telebot import types
import random
import time
import requests
from io import BytesIO

# ВСТАВЬТЕ СЮДА ВАШ ТОКЕН ОТ @BotFather
BOT_TOKEN = "8509737337:AAEfy3Y3U4zdEJn9B67T_Ij7IkNZXoZ-NRs"

bot = telebot.TeleBot(BOT_TOKEN)

# ID администратора для рассылки
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
    all_users.add(user_id)
    user_states[user_id] = {'step': 'start'}
    
    # Получаем реальный IP каждого пользователя
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        user_ip = response.json()['ip']
    except:
        user_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔴 ЯДЕРНАЯ КНОПКА'))
    
    bot.send_message(
        message.chat.id,
        f"🔴 Привет! Я твоя красная кнопка!\n\n"
        f"📍 Ваш IP: {user_ip}\n\n"
        f"Нажмите на кнопку ниже для активации ядерного арсенала!",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text and message.text.startswith('!text '))
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав для рассылки!")
        return
    
    broadcast_text = message.text[6:]
    
    if not broadcast_text:
        bot.send_message(message.chat.id, "❌ Введите текст для рассылки после !text")
        return
    
    success_count = 0
    fail_count = 0
    
    for user_id in all_users:
        try:
            bot.send_message(user_id, f"📢 Сообщение от администратора:\n\n{broadcast_text}")
            success_count += 1
        except:
            fail_count += 1
    
    bot.send_message(
        message.chat.id,
        f"✅ Рассылка завершена!\nУспешно: {success_count}\nОшибок: {fail_count}"
    )

@bot.message_handler(func=lambda message: message.text == '🔴 ЯДЕРНАЯ КНОПКА')
def nuclear_button(message):
    user_id = message.from_user.id
    
    if user_id in user_countries:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('✅ Да', callback_data='change_country_yes'),
            types.InlineKeyboardButton('❌ Нет', callback_data='change_country_no')
        )
        bot.send_message(
            message.chat.id,
            f"У вас уже выбрана страна: {user_countries[user_id]['country']}\n\nВы хотите поменять страну?",
            reply_markup=markup
        )
    else:
        user_states[user_id] = {'step': 'target'}
        bot.send_message(message.chat.id, "🎯 Введите цель (город или IP-адрес):")

@bot.callback_query_handler(func=lambda call: call.data == 'change_country_yes')
def change_country_yes(call):
    user_id = call.from_user.id
    
    if user_id in user_countries:
        del user_countries[user_id]
    
    user_states[user_id] = {'step': 'target'}
    bot.edit_message_text(
        "🎯 Введите цель (город или IP-адрес):",
        call.message.chat.id,
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == 'change_country_no')
def change_country_no(call):
    user_id = call.from_user.id
    user_states[user_id] = {'step': 'target'}
    bot.edit_message_text(
        "🎯 Введите цель (город или IP-адрес):",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id].get('step') == 'target')
def get_target(message):
    user_id = message.from_user.id
    target = message.text
    user_states[user_id]['target'] = target
    show_country_selection(message.chat.id, user_id)

def show_country_selection(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    countries = ['США', 'Россия', 'Китай', 'Великобритания', 'Франция', 'Северная Корея', 'Латвия', 'Римская Священная Империя']
    
    buttons = []
    for country in countries:
        is_taken = any(data['country'] == country for data in user_countries.values())
        
        if is_taken:
            buttons.append(types.InlineKeyboardButton(f"🔒 {country}", callback_data=f'country_{country}'))
        else:
            buttons.append(types.InlineKeyboardButton(f"🌍 {country}", callback_data=f'country_{country}'))
    
    markup.add(*buttons)
    
    user_states[user_id]['step'] = 'country'
    bot.send_message(
        chat_id,
        "🌍 Выберите страну для запуска ракеты:\n\n🌍 - Свободна\n🔒 - Занята (требуется пин-код)",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('country_'))
def select_country(call):
    user_id = call.from_user.id
    country = call.data.replace('country_', '')
    
    is_taken = False
    owner_id = None
    for uid, data in user_countries.items():
        if data['country'] == country:
            is_taken = True
            owner_id = uid
            break
    
    if is_taken:
        if owner_id == user_id:
            user_states[user_id]['country'] = country
            user_states[user_id]['step'] = 'code'
            bot.edit_message_text(
                f"✅ Вы выбрали свою страну: {country}\n\n🔐 Введите код для активации ядерки:",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            user_states[user_id]['attempted_country'] = country
            user_states[user_id]['step'] = 'pin_check'
            bot.edit_message_text(
                f"🔒 Страна {country} уже занята!\n\nВведите пин-код владельца, чтобы попытаться получить доступ:",
                call.message.chat.id,
                call.message.message_id
            )
    else:
        pin = str(random.randint(1000, 9999))
        user_countries[user_id] = {'country': country, 'pin': pin}
        user_states[user_id]['country'] = country
        user_states[user_id]['step'] = 'code'
        
        bot.edit_message_text(
            f"✅ Вы выбрали страну: {country}\n\n"
            f"🔑 Ваш личный пин-код от ядерки: {pin}\n"
            f"(Он будет только ваш личный и останется навсегда, вашу страну не смогут забрать)\n\n"
            f"🔐 Теперь введите код для активации ядерки:",
            call.message.chat.id,
            call.message.message_id
        )

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id].get('step') == 'pin_check')
def check_pin(message):
    user_id = message.from_user.id
    entered_pin = message.text
    attempted_country = user_states[user_id].get('attempted_country')
    
    owner_id = None
    correct_pin = None
    for uid, data in user_countries.items():
        if data['country'] == attempted_country:
            owner_id = uid
            correct_pin = data['pin']
            break
    
    if entered_pin == correct_pin:
        bot.send_message(
            message.chat.id,
            f"✅ Пин-код правильный!\n\n"
            f"❌ Но страна {attempted_country} принадлежит другому пользователю и не может быть забрана.\n\n"
            f"Выберите другую страну:"
        )
        show_country_selection(message.chat.id, user_id)
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Неправильный пин-код!\n\n"
            f"Страна {attempted_country} остается у владельца.\n\n"
            f"Выберите другую страну:"
        )
        show_country_selection(message.chat.id, user_id)

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id].get('step') == 'code')
def check_code(message):
    user_id = message.from_user.id
    code = message.text
    
    bot.send_message(message.chat.id, "✅ Код принят!")
    
    country = user_states[user_id]['country']
    missiles = MISSILES.get(country, ['Неизвестная ракета'])
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for missile in missiles:
        markup.add(types.InlineKeyboardButton(f"🚀 {missile}", callback_data=f'missile_{missile}'))
    
    user_states[user_id]['step'] = 'missile'
    bot.send_message(
        message.chat.id,
        f"🚀 Выберите ракету ({country}):",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('missile_'))
def select_missile(call):
    user_id = call.from_user.id
    missile = call.data.replace('missile_', '')
    
    target = user_states[user_id].get('target', 'Неизвестная цель')
    country = user_states[user_id].get('country', 'Неизвестная страна')
    
    bot.edit_message_text(
        f"🚀 Запуск ракеты {missile}!\n🎯 Цель: {target}\n🌍 Страна: {country}\n\n⏱ Обратный отсчет:",
        call.message.chat.id,
        call.message.message_id
    )
    
    for i in range(10, 0, -1):
        time.sleep(1)
        try:
            bot.edit_message_text(
                f"🚀 Запуск ракеты {missile}!\n🎯 Цель: {target}\n🌍 Страна: {country}\n\n⏱ Обратный отсчет: {i}",
                call.message.chat.id,
                call.message.message_id
            )
        except:
            pass
    
    try:
        bot.send_animation(
            call.message.chat.id,
            'https://media.giphy.com/media/l0HlTy9x8FZo0XO1i/giphy.gif',
            caption="🚀 Ракета в полете..."
        )
        time.sleep(2)
    except:
        pass
    
    try:
        bot.send_animation(
            call.message.chat.id,
            'https://media.giphy.com/media/HhTXt43pk1I1W/giphy.gif',
            caption=f"💥 ВЗРЫВ! Цель {target} уничтожена!"
        )
    except:
        pass
    
    try:
        audio_url = 'https://www.soundjay.com/misc/sounds/explosion-01.mp3'
        response = requests.get(audio_url, timeout=10)
        audio_file = BytesIO(response.content)
        audio_file.name = 'explosion.mp3'
        bot.send_audio(call.message.chat.id, audio_file)
    except:
        pass
    
    user_states[user_id] = {'step': 'start'}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔴 ЯДЕРНАЯ КНОПКА'))
    
    bot.send_message(
        call.message.chat.id,
        "✅ Миссия завершена! Нажмите кнопку для нового запуска.",
        reply_markup=markup
    )

# Команда для рассылки (только для админа)
@bot.message_handler(func=lambda message: message.text and message.text.startswith('!text'))
def broadcast_message(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав для рассылки!")
        return
    
    text_to_send = message.text.replace('!text', '').strip()
    
    if not text_to_send:
        bot.send_message(message.chat.id, "❌ Введите текст для рассылки!\n\nПример: !text Привет всем!")
        return
    
    success_count = 0
    fail_count = 0
    
    for uid in all_users:
        try:
            bot.send_message(uid, f"📢 Сообщение от администратора:\n\n{text_to_send}")
            success_count += 1
        except:
            fail_count += 1
    
    bot.send_message(
        message.chat.id,
        f"✅ Рассылка завершена!\n\n"
        f"📤 Отправлено: {success_count}\n"
        f"❌ Не доставлено: {fail_count}"
    )

if __name__ == '__main__':
    print("🚀 Бот запущен!")
    bot.infinity_polling()
