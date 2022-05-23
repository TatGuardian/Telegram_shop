import telebot
import pymysql

from telebot import types, TeleBot
import threading
from requests import get
from time import sleep

bot = TeleBot('Token')
db = pymysql.connect(database='shop_seashop', host="localhost", port=port, user="root",
                     password="password")  
lock = threading.Lock()  # locks threading until it is unlocked
sql = db.cursor()

# working with database
sql.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT, nick TEXT, cash INT, access INT, bought INT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS shop (id INT, name TEXT, price INT, goods TEXT, consumer TEXT)""")
db.commit()


def tocat(message, chatid):
    cid=chatid
    try:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton(text="Краб", callback_data="catalog_crab"),
            types.InlineKeyboardButton(text="Лосось", callback_data="catalog_salmon"),
            types.InlineKeyboardButton(text="Икра", callback_data="catalog_caviar_forel"),
            types.InlineKeyboardButton(text="Морской ёж", callback_data="catalog_hedgehog")
        )
        bot.delete_message(message.chat.id, message_id=message.id)
        bot.send_message(message.chat.id, reply_markup=keyboard, text="Каталог товаров:")
    except:
        bot.send_message(cid, f"unknown mistake")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.InlineKeyboardButton(text="Корзина", callback_data="mylist"),
        types.InlineKeyboardButton(text="Каталог", callback_data="catalogue"),
        types.InlineKeyboardButton(text="Доставка", callback_data="delivery"),
        types.InlineKeyboardButton(text="Оставить отзыв", callback_data="feedback"),

    )
    cid = message.chat.id
    try:
        name_nick = message.from_user.first_name
        uid = message.from_user.id
        sql.execute(f"SELECT id FROM users WHERE id={uid}")
        if sql.fetchone() is None:
            sql.execute(
                f"INSERT INTO users (id, nick, cash, access, bought) VALUES ('{uid}', '{name_nick}', '0', '0', '0')")
            bot.send_message(cid, f"{name_nick}, welcome to  Seashop!", reply_markup=markup)
            db.commit()
        else:
            bot.send_message(cid, f"You're already registered", reply_markup=markup)
    except:
        bot.send_message(cid, f"unknown mistake")


@bot.message_handler(commands=['profile'])
def profile(message):
    cid = message.chat.id
    try:
        uid = message.from_user.id
        sql.execute(f"SELECT * FROM users WHERE id='{uid}'")
        getaccess = sql.fetchone()[3]
        if getaccess == 0:
            access = "Пользователь"
        elif getaccess == 1:
            access = "админ"
        elif getaccess == 2:
            access = "разработчик"
        sql.execute(f"SELECT * FROM users WHERE id={cid}")
        query = sql.fetchall()
        for info in query:
            bot.send_message(cid,
                             f"Твой профиль:\nВаш ID: {info[0]}\nБаланс: {info[2]}\nУровень доступа: {access}\nКуплено товаров: {info[4]}\n",
                             parse_mode='Markdown')
    except:
        bot.send_message(cid, f"unknown mistake")


@bot.message_handler(commands=['users'])
def seeusers(message):
    cid = message.chat.id
    try:
        text = "All users:\n"
        user = 0
        uid = message.from_user.id
        sql.execute(f"SELECT * FROM users WHERE id='{uid}'")
        getaccess = sql.fetchone()[3]
        need_access = 1
        if getaccess < need_access:
            bot.send_message(cid, f"You don't have access")
        else:  # getaccess >= need_access:
            sql.execute(f"SELECT * FROM users")
            query = sql.fetchall()
            for info in query:
                if info[3] == 0:
                    access = "Пользователь"
                elif info[3] == 1:
                    access = "админ"
                elif info[3] == 2:
                    access = "разработчик"
                user += 1
                text += f"{user}: Name= {info[1]}, ID= {info[0]}, Balance= {info[2]}, Access= {access}, Bought= {info[4]}\n"
            bot.send_message(cid,
                             text=text,
                             parse_mode='Markdown')
    except:
        bot.send_message(cid, f"unknown mistake")


@bot.message_handler(commands=['mylist'])
def mylist(message):
    cid = message.chat.id
    try:
        uid = message.from_user.id
        text = "Список купленных товаров:"
        sql.execute(f"SELECT * FROM users WHERE id='{uid}'")
        query = sql.fetchone()
        for info in query:
            sql.execute(f"SELECT * FROM shop")
            query_1 = sql.fetchone()
            if query_1 is not None:
                for shop in query_1:
                    if str(info[0]) in shop[4]:
                        # we're checking if the user exists in shop table, ei if he has bought anything
                        text += f" id: '{info[0]}', '{shop[1]}', goods: '{shop[3]}', price: '{shop[2]}'\n"
        if text == "Список купленных товаров:":
            text += f" ничего еще не куплено =("
        bot.send_message(cid, f"{text}", parse_mode='Markdown')
    except:
        bot.send_message(cid, f"unknown mistake")


@bot.callback_query_handler(
    func=lambda c: c.data == "catalog_crab" or c.data == "catalog_salmon" or c.data == "catalog_caviar_forel"
                   or c.data == "catalog_hedgehog")
def catalogue(callback):  # добавить айди к каждому товару
    cid = callback.message.chat.id
    uid = callback.message.from_user.id
    if callback.data == "catalog_crab":
        try:
            bot.delete_message(message_id=callback.message.id, chat_id=cid)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton(text="Добавить в корзину", callback_data="add_crab"),
                # types.InlineKeyboardButton(text=""),
                types.InlineKeyboardButton(text="Назад в каталог", callback_data="to_catalogue")
            )
            bot.send_photo(caption="Камчатский краб\nЦена: 2200 ₽ за 1 кг", chat_id=cid,
                           photo=open("C:/Users/user/PycharmProjects/Telexram/shop/pictures/crab.jpg", "rb"),
                           reply_markup=keyboard)
        except:
            bot.send_message(cid, f"unknown mistake")

    elif callback.data == "catalog_salmon":
        try:
            bot.delete_message(message_id=callback.message.id, chat_id=cid)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton(text="Добавить в корзину", callback_data="add_salmon"),
                # types.InlineKeyboardButton(text=""),
                types.InlineKeyboardButton(text="Назад в каталог", callback_data="to_catalogue")
            )
            bot.send_photo(caption="Лосось\nЦена: 1600 ₽ за 1 кг", chat_id=cid,
                           photo=open("C:/Users/user/PycharmProjects/Telexram/shop/pictures/salmon.jpg", "rb"),
                           reply_markup=keyboard)
        except:
            bot.send_message(cid, f"unknown mistake")

    elif callback.data == "catalog_caviar_forel":
        try:
            bot.delete_message(message_id=callback.message.id, chat_id=cid)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton(text="Добавить в корзину", callback_data="add_caviar_forel"),
                # types.InlineKeyboardButton(text=""),
                types.InlineKeyboardButton(text="Назад в каталог", callback_data="to_catalogue")
            )
            bot.send_photo(caption="Икра красная (форель)\nЦена: 2880 ₽ за 500г", chat_id=cid,
                           photo=open("C:/Users/user/PycharmProjects/Telexram/shop/pictures/caviar_forel.jpg", "rb"),
                           reply_markup=keyboard)
        except:
            bot.send_message(cid, f"unknown mistake")
    elif callback.data == "catalog_hedgehog":
        try:
            bot.delete_message(message_id=callback.message.id, chat_id=cid)
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton(text="Добавить в корзину", callback_data="add_hedgehog"),
                # types.InlineKeyboardButton(text=""),
                types.InlineKeyboardButton(text="Назад в каталог", callback_data="to_catalogue")
            )
            bot.send_photo(caption="Морской ёж\nЦена: 200 ₽ за шт", chat_id=cid,
                           photo=open("C:/Users/user/PycharmProjects/Telexram/shop/pictures/hedgehog.jpg", "rb"),
                           reply_markup=keyboard)
        except:
            bot.send_message(cid, f"unknown mistake")


@bot.callback_query_handler(func=lambda call: call.data == "to_catalogue")
def to_catalogue(callback):
    msg = callback.message
    cid = msg.chat.id
    try:
        tocat(msg, cid)
    except:
        bot.send_message(cid, f"unknown mistake")

@bot.message_handler(content_types=['text'])
def mylist(message):
    cid = message.chat.id
    if message.text == 'Корзина':
        try:
            uid = message.from_user.id
            text = "Список купленных товаров:"
            sql.execute(f"SELECT * FROM users WHERE id='{uid}'")
            query = sql.fetchone()
            for info in query:
                sql.execute(f"SELECT * FROM shop")
                query_1 = sql.fetchone()
                if query_1 is not None:
                    for shop in query_1:
                        if str(info[0]) in shop[4]:
                            # we're checking if the user exists in shop table, ei if he has bought anything
                            text += f" id: '{info[0]}', '{shop[1]}', goods: '{shop[3]}', price: '{shop[2]}'\n"
            if text == "Список купленных товаров:":
                text += f" ничего еще не куплено =("
            bot.send_message(cid, f"{text}", parse_mode='Markdown')
        except:
            bot.send_message(cid, f"unknown mistake")
    elif message.text == 'Каталог':
        try:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton(text="Краб", callback_data="catalog_crab"),
                types.InlineKeyboardButton(text="Лосось", callback_data="catalog_salmon"),
                types.InlineKeyboardButton(text="Икра", callback_data="catalog_caviar_forel"),
                types.InlineKeyboardButton(text="Морской ёж", callback_data="catalog_hedgehog")
            )
            bot.send_message(message.chat.id, reply_markup=keyboard, text="Каталог товаров:")
        except:
            bot.send_message(cid, f"unknown mistake")
    elif message.text == 'Доставка':
        pass
    elif message.text == 'Оставить отзыв':
        pass
    else:
        pass


bot.polling(non_stop=True)
