import telebot
from telebot import types
import requests
import json
import dpath.util
from datetime import date
import sqlite3
token = '5544422800:AAEXe6nYx9Sp67IzjZUe7cys-2fIedO6XM0'
bot = telebot.TeleBot(token)
city = None
lat = None
lon = None

with sqlite3.connect("weather.db") as db:
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS weather(
        user_id INTEGER PRIMARY KEY,
        city VARCHAR(40),
        lat REAL,
        lon REAL
    )""")

@bot.message_handler(commands=['start'])
def startmsg(message):
     sg = bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!👋\n\nЯ - бот с самой точной погодой во всём телеграме! Напиши мне свой город, чтобы я мог сделать прогноз ⬇️")
     bot.register_next_step_handler(sg, city_choose)

@bot.message_handler(content_types=['text'])
def weather2(message):
    if message.text == "Узнать Погоду":
        weather(message)
    elif message.text == "Погода Неверная":
        bot.send_message(message.chat.id, "Пошёл нахуй все верное.")
    elif message.text == "Сменить Город":
        asa = bot.send_message(message.chat.id, "Напиши город на который хочешь сменить")
        bot.register_next_step_handler(asa, change_city)

def city_choose(message):
    db = sqlite3.connect("weather.db")
    cursor = db.cursor()
    user_id = message.from_user.id
    city = message.text
    resp = requests.get(url=f"https://geocode-maps.yandex.ru/1.x/?apikey=f75f2782-6c2e-438d-bfb3-77be826cff57&format=json&geocode={city}")
    jresp = json.loads(resp.text)
    try:
     coords = jresp.get("response").get("GeoObjectCollection").get("featureMember")
    except AttributeError:
        bot.send_message(message.chat.id, "Вы ввели неверное название")
        city = None
    except IndexError:
        bot.send_message(message.chat.id, "Вы ввели неверное название")
        city = None
    item = coords[0]
    coords_final = dpath.util.get(item, "GeoObject/Point/pos")
    words = coords_final.split()
    lat = words[0]
    lon = words[1]
    print(lat, lon)
    try:
        cursor.execute("INSERT INTO weather(user_id, city, lat, lon) VALUES(?, ?, ?, ?);",(user_id, city, lat, lon))
        db.commit()
        cursor.execute("SELECT city FROM weather WHERE user_id = ?;",(user_id,))
        bbb = cursor.fetchone()
        print(bbb)
    except sqlite3.Error as e:
        print("Error ", e)
    bot.send_message(message.chat.id, "Хорошо, сейчас подготовлю для тебя прогноз погоды...")
    weather(message)

def weather(message):
    city = None
    lat = None
    lon = None
    user_id = message.from_user.id
    db = sqlite3.connect("weather.db")
    cursor = db.cursor()
    try:
        cursor.execute("SELECT city, lat, lon FROM weather WHERE user_id = ?;",(user_id,))
        pre = cursor.fetchone()
        city = pre[0]
        lat = pre[2]
        lon = pre[1]
    except sqlite3.Error as e:
        print("Error ", e)
    print(city, lat, lon)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('Узнать Погоду')
    btn2 = types.KeyboardButton('Сменить Город')
    btn3 = types.KeyboardButton('Погода Неверная')
    markup.add(btn, btn2, btn3)
    resp = requests.get(url=f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}", headers={"X-Yandex-API-Key" : "8e45e1a6-86fb-44ce-8035-480574a446df"})
    jresp = json.loads(resp.text)
    temp = jresp.get("fact").get("temp")
    pre_condition = jresp.get("fact").get("condition")
    if pre_condition == "overcast":
        condition = "☁️ Пасмурно"
    elif pre_condition == "partly-cloudy":
        condition = "⛅️ Малооблачно"
    elif pre_condition == "clear":
        condition = "☀️ Ясно"
    elif pre_condition == "cloudy":
        condition = "🌥 Облачно с прояснениями"
    elif pre_condition == "drizzle":
        condition = "💧 Мелкий дождь (морось)"
    elif pre_condition == "light-rain":
        condition = "💦 Небольшой дождь"
    elif pre_condition == "rain":
        condition = "🌧 Дождь"
    elif pre_condition == "moderate-rain":
        condition = "🌧 Умеренно сильный дождь"
    elif pre_condition == "heavy-rain":
        condition = "🌧 Сильный дождь"
    elif pre_condition == "continous-heavy-rain":
        condition = "🌧 Продолжительный сильный дождь"
    elif pre_condition == "showers":
        condition = "🌊 Ливень"
    elif pre_condition == "wet-snow":
        condition = "🌨 Снег с дождём"
    elif pre_condition == "snow":
        condition = "❄️ Снег"
    elif pre_condition == "thunderstorm":
        condition = "🌩 Гроза"
    elif pre_condition == "thunderstorm-with-rain":
        condition = "⛈ Дождь с грозой"
    feels_like = jresp.get("fact").get("feels_like")
    yesterday = jresp.get("yesterday").get("temp")
    water_temp = jresp.get("fact").get("temp_water")
    if water_temp == None:
        water_temp = "Нет данных"
    curr_date = date.today()
    bot.send_message(message.chat.id, f"Погода в {city} на {curr_date}:\n\n{condition} +{temp}\nОщущается как: {feels_like}\nВчера: {yesterday}\nТемпература воды: {water_temp}", reply_markup=markup)

def change_city(message):
    db = sqlite3.connect("weather.db")
    cursor = db.cursor()
    user_id = message.from_user.id
    try:
        city = message.text
        resp = requests.get(url=f"https://geocode-maps.yandex.ru/1.x/?apikey=f75f2782-6c2e-438d-bfb3-77be826cff57&format=json&geocode={city}")
        jresp = json.loads(resp.text)
        try:
            coords = jresp.get("response").get("GeoObjectCollection").get("featureMember")
        except AttributeError:
         bot.send_message(message.chat.id, "Вы ввели неверное название")
         city = None
        except IndexError:
         bot.send_message(message.chat.id, "Вы ввели неверное название")
         city = None
        item = coords[0]
        coords_final = dpath.util.get(item, "GeoObject/Point/pos")
        words = coords_final.split()
        lat = words[0]
        lon = words[1]
        print(lat, lon)
        cursor.execute("UPDATE weather SET city = ? WHERE user_id = ?;",(city,user_id))
        cursor.execute("UPDATE weather SET lat = ? WHERE user_id = ?;",(lat,user_id))
        cursor.execute("UPDATE weather SET lon = ? WHERE user_id = ?;",(lon,user_id))
        db.commit()
    except sqlite3.Error as e:
        print("SQL error: ", e)
    weather(message)


bot.infinity_polling()
