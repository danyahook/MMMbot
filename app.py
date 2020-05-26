#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python Libraries
import hashlib
import telebot as tb
from threading import Thread
import traceback
import schedule
import time
from telebot import apihelper
from functools import wraps

# Custom Modules
from modules.dbhelper import DBHelper
import modules.names as names

db = DBHelper()

# ip = '59.124.224.180'
# port = '3128'
#
#
# apihelper.proxy = {
#     'https': 'https://{}:{}'.format(ip, port)
# }


def schedule_start():
    while 1:
        schedule.run_pending()
        time.sleep(1)


def daily_bonus():
    user_per = db.get_percent(1)[-1] / 100 + 1
    invest_per = db.get_percent(2)[-1] / 100 + 1

    db.capitalization(user_per)
    db.capitalization_invest(invest_per)


def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def valid_user(bot):
    def decorator(fn):
        @wraps(fn)
        def wrapped(message):
            chanel = bot.get_chat_member(names.CHANNEL_ID, message.from_user.id)

            if chanel.status == 'left':
                bot.send_message(message.from_user.id,
                                 text=f'❌ Вы не подписанны на <a href="{names.CHANNEL_LINK}">канал</a>',
                                 parse_mode='HTML')
                return False

            if fn.__name__ == 'start':
                return True
            else:
                return fn(message)

        return wrapped

    return decorator


def user_info(fn):
    @wraps(fn)
    def wrapped(message):
        user = None
        user_data = db.get_info(str(message.from_user.id))

        if len(user_data) != 0:
            user = dict(zip(names.db_keys, user_data[0]))

        return fn(message, user)

    return wrapped


def create_bot(api):
    bot = tb.TeleBot(api)

    @bot.message_handler(commands=['start'])
    @user_info
    def start(message, user):
        href = message.text[7: len(message.text)]
        status = valid_user(bot)(start)(message)

        if user and status and message.text == '/start':
            hid = hashlib.md5(str(message.from_user.id).encode('utf-8')).hexdigest()
            user_name = message.from_user.first_name

            if message.from_user.last_name is not None:
                user_name += f' {message.from_user.last_name}'

            db.add_user(message.from_user.id, hid, user_name, 0)
        elif len(href) != 0 and len(db.get_user_by_hid(href)) != 0:
            chanel = bot.get_chat_member(names.CHANNEL_ID, message.from_user.id)

            if chanel.status != 'left':
                keyboard = tb.types.InlineKeyboardMarkup()
                channel_button = tb.types.InlineKeyboardButton(text='🔗 Ссылка на канал', url=names.CHANNEL_LINK)
                chat_button = tb.types.InlineKeyboardButton(text='🔗 Ссылка на чат',
                                                            url=names.GROUP_LINK)
                confirm_button = tb.types.InlineKeyboardButton(text='📌 Подтвердить', callback_data=href)
                keyboard.add(channel_button)
                keyboard.add(chat_button)
                keyboard.add(confirm_button)

                bot.send_message(message.from_user.id,
                                 '📍 <b>Инструкция:</b>\nДля начала работы с ботом, Вам необходимо подписаться на канал'
                                 ' и вступить в группу. После проделанных действий вернитесь в бот и нажмите кнопку '
                                 '"Подтвердить"',
                                 disable_notification=True, reply_markup=keyboard, parse_mode='HTML')
            else:
                bot.send_message(message.from_user.id, "❌ Вы уже и так подписаны на данные чат и канал! ")
        else:
            user_btn = tb.types.ReplyKeyboardMarkup(True)
            user_btn.row(names.REF_LINK, names.ADD_TO)
            user_btn.row(names.BANK, names.TAKE_BANK)
            user_btn.row(names.ADDRESS, names.ABOUT_US)
            bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    @bot.message_handler(func=lambda message: message.text == names.BANK)
    @valid_user(bot)
    @user_info
    def get_bank(message, user):
        if user['rate'] == 0:
            bot.send_message(message.from_user.id,
                             text=f'💳 Ваш баланс {user["balance"]:.2f} USDN. Вы еще не можете его выводить,'
                                  f'для вывода пригласите 5 человек.')
        elif user['rate'] < 5:
            bot.send_message(message.from_user.id,
                             text=f'💳 Ваш баланс {user["balance"]:.2f} USDN. Вы еще не можете его выводить, '
                                  f'для вывода пригласите еще {5 - user["rate"]} человек. '
                                  f'На данный момент вы пригласили {user["rate"]} пользователей.')
        else:
            bot.send_message(message.from_user.id,
                             text=f'Вывод средств доступен ✅\n💳 На вашем балансе: {user["balance"]:.2f} USDN.')

    @bot.message_handler(func=lambda message: message.text == names.REF_LINK)
    @valid_user(bot)
    @user_info
    def get_ref_link(message, user):
        bot.send_message(message.from_user.id,
                         text=f'🧷 Ваша реферальная ссылка: https://t.me/usdn_bot?start={user["user_hash"]}\n'
                              f'Приглашайте людей по ссылке выше и получайте бонусы')

    @bot.message_handler(func=lambda message: message.text == names.ABOUT_US)
    @valid_user(bot)
    def get_about_us(message):
        text = db.get_btn_text(3)[-1]
        bot.send_message(message.from_user.id,
                         text=text)

    @bot.message_handler(func=lambda message: message.text == names.TAKE_BANK)
    @valid_user(bot)
    @user_info
    def take_bank(message, user):
        if user['balance'] < 100:
            bot.send_message(message.from_user.id,
                             text='📌 - Вывод доступен от 100 долларов\n'
                                  f'- Для вывода Вам не хватает {100 - user["balance"]:.2f} долларов\n'
                                  '- Вы можете заработать недостающую сумму, активно приглашая участников в систему, '
                                  'и получать за каждого приглашённого 1 USDN на баланс\n'
                                  '- Также Ваш баланс ежедневно растёт на 0.5%\n'
                                  '- Вы можете стать инвестором системы, получая двойной % на свой баланс.')
        else:
            text = db.get_btn_text(2)[-1]
            bot.send_message(message.from_user.id,
                             text=text)

    @bot.message_handler(func=lambda message: message.text == names.ADDRESS)
    @valid_user(bot)
    @user_info
    def get_address(message, user):
        if user['address'] is None:
            msg = bot.send_message(message.from_user.id, "🔗 Укажите свой ETH Адрес, взяв его в кошельке TRUST "
                                                         "trustwallet.com/ru:")
            bot.register_next_step_handler(msg, set_address)
        else:
            bot.send_message(message.from_user.id, f'🗃 Адрес вашего кошелька: {user["address"]}\n'
                                                   f'Для изменения введите /change')

    def set_address(message):
        if message.content_type == 'text' and len(message.text) < 128:
            db.btc_address(str(message.from_user.id), message.text)
            bot.send_message(message.from_user.id, "Адрес успешно установлен")
        else:
            msg = bot.send_message(message.from_user.id, "🔗 Укажите свой ETH Адрес, взяв его в кошельке TRUST "
                                                         "trustwallet.com/ru:")
            bot.register_next_step_handler(msg, set_address)

    @bot.message_handler(commands=['change'])
    @valid_user(bot)
    def change_address(message):
        msg = bot.send_message(message.from_user.id, "🔗 Укажите свой ETH Адрес, взяв его в кошельке TRUST "
                                                     "trustwallet.com/ru:")
        bot.register_next_step_handler(msg, set_address)

    @bot.callback_query_handler(func=lambda call: len(call.data) == 32)
    @valid_user(bot)
    @user_info
    def callback_inline(call, user):
        if not user:
            bot.delete_message(call.message.chat.id, call.message.message_id)

            user_info_by_hid = db.get_user_by_hid(call.data)[0]
            user = dict(zip(names.db_keys, user_info_by_hid[0]))

            if user['rate'] < 50:
                db.rate_update_by_hid(call.data)
                if user['rate'] == 4:
                    db.is_valid(call.data)

            hid = hashlib.md5(str(call.from_user.id).encode('utf-8')).hexdigest()
            user_name = call.from_user.first_name

            if call.from_user.last_name is not None:
                user_name += f' {call.from_user.last_name}'

            db.add_user(call.from_user.id, hid, user_name, 0)

            bot.send_message(user['user_id'], text=f'👌 <a href="tg://user?id={user["user_id"]}">{user_name}</a> '
                                           f'подписался по вашей ссылке!', parse_mode='HTML')
            bot.send_message(call.from_user.id,
                             text='✅ Вы выполнили условия!')
            bot.send_message(call.from_user.id,
                             text='Для начала работы введите /start')
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.from_user.id,
                             text='❌ Вы уже принимали приглашения!')

    @bot.message_handler(commands=['admin'])
    @valid_user(bot)
    def admin(message):
        msg = bot.send_message(message.from_user.id, "⚙ Укажите пароль для входа в админ-панель (для отмены No):")
        bot.register_next_step_handler(msg, is_admin)

    def is_admin(message):
        admin_pass = db.admin()[-1]
        if admin_pass == message.text:
            admin_menu(message)
        elif message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Ввод прерван")
        else:
            msg = bot.send_message(message.from_user.id, "⚙ Неверный пароль, введите вновь (для отмены No):")
            bot.register_next_step_handler(msg, is_admin)

    def admin_menu(message):
        user_btn = tb.types.ReplyKeyboardMarkup(True)
        user_btn.row(names.ALL_PEOPLE, names.VALID_PEOPLE, names.MAILING)
        user_btn.row(names.CHANGE_BALANCE, names.MAKE_AN_INVESTOR, names.STOP_INVESTOR)
        user_btn.row(names.P_DAY)
        user_btn.row(names.P_WEAK)
        user_btn.row(names.P_MOUNT)
        bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    def get_admin_info(message, users):
        info = str()

        for user in users:
            user = dict(zip(names.db_keys, user))

            invest = '💎' if user['invest'] else '🌐'
            info += f'[{user["id"]}] {invest} <a href="tg://user?id={user["user_id"]}">{user["user_name"]}</a> - ' \
                    f'{user["rate"]}\n'

        bot.send_message(message.from_user.id, text=info,
                         parse_mode='HTML', disable_notification=True)

    @bot.message_handler(func=lambda message: message.text == names.ALL_PEOPLE)
    @valid_user(bot)
    def all_people(message):
        users = db.get_info_all()
        count_of_users = len(users)

        bot.send_message(message.from_user.id, f'✏️ Пользователей всего: {count_of_users}')
        if count_of_users != 0:
            get_admin_info(message, users)

    @bot.message_handler(func=lambda message: message.text == names.VALID_PEOPLE)
    @valid_user(bot)
    def valid_people(message):
        users = db.get_valid_users()
        count_of_users = len(users)

        bot.send_message(message.from_user.id, f'✏️ Пользователей, выполнивших условие: {count_of_users}')
        if count_of_users != 0:
            get_admin_info(message, users)

    @bot.message_handler(func=lambda message: message.text == names.ADD_TO)
    @valid_user(bot)
    def add_to(message):
        text = db.get_btn_text(1)[-1]
        bot.send_message(
            message.from_user.id,
            text=text
        )

    @bot.message_handler(func=lambda message:
                         message.text == names.P_DAY or message.text == names.P_WEAK or message.text == names.P_MOUNT)
    @valid_user(bot)
    def valid_people(message):

        if message.text == names.P_MOUNT:
            interval, interval_ru = 'start of month', 'месяц'
        elif message.text == names.P_WEAK:
            interval, interval_ru = '-6 days', 'неделю'
        else:
            interval, interval_ru = 'start of day', 'день'

        users = db.get_between_time(interval)
        count_of_users = len(users)

        bot.send_message(message.from_user.id, f'✏️ Пользователей за {interval_ru}: {count_of_users}')
        if count_of_users != 0:
            get_admin_info(message, users)

    @bot.message_handler(func=lambda message: message.text == names.CHANGE_BALANCE)
    @valid_user(bot)
    def change_balance(message):
        msg = bot.send_message(message.from_user.id, "⚙ Укажите ID(цифра) пользователя, чей баланс нужно "
                                                     "изменить (для отмены No):")
        bot.register_next_step_handler(msg, get_user)

    def get_user(message):
        if is_number(message.text):
            user_info_by_id = db.get_balance_by_id(message.text)

            if len(user_info_by_id) == 0:
                bot.send_message(message.from_user.id, "⚙ Пользователь с таким ID не найден!")
                return

            user = dict(zip(names.db_keys, user_info_by_id[0]))
            msg = bot.send_message(message.from_user.id,
                                   f'Баланс <a href="tg://user?id={user["user_id"]}">{user["user_name"]}</a>: '
                                   f'{user["balance"]} USDN. Введите значение для смены или введите "No" для отмены:',
                                   parse_mode='HTML')
            bot.register_next_step_handler(msg, lambda m: set_balance(m, user["user_id"]))
        elif message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция смены баланса прервана")
        else:
            msg = bot.send_message(message.from_user.id, "⚙ ID должен быть цифрой:")
            bot.register_next_step_handler(msg, get_user)

    def set_balance(message, user_id):
        if is_number(message.text):
            db.set_balance_by_id(user_id, message.text)
            bot.send_message(message.from_user.id, "⚙ Баланс успешно изменен")
        elif message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция смены баланса прервана")
        else:
            msg = bot.send_message(message.from_user.id, "⚙ Баланс может быть только цифрой (для отмены No):")
            bot.register_next_step_handler(msg, lambda m: set_balance(m, user_id))

    @bot.message_handler(func=lambda message: message.text == names.MAKE_AN_INVESTOR)
    @valid_user(bot)
    def make_investor(message):
        msg = bot.send_message(message.from_user.id, "⚙ Укажите ID(цифра) пользователя, которого сделать инвестором "
                                                     "(для отмены No): ")
        bot.register_next_step_handler(msg, lambda m: investor(m, 1))

    @bot.message_handler(func=lambda message: message.text == names.STOP_INVESTOR)
    @valid_user(bot)
    def make_investor(message):
        msg = bot.send_message(message.from_user.id, "⚙ Укажите ID(цифра) пользователя, которого исключить из "
                                                     "инвесторов (для отмены No): ")
        bot.register_next_step_handler(msg, lambda m: investor(m, 0))

    def investor(message, status):
        if is_number(message.text):
            db.set_invest(message.text, status)
            db.is_valid_by_id(message.text, 0) if status == 0 else db.is_valid_by_id(message.text, 1)
            bot.send_message(message.from_user.id, "⚙ Статус инвестора изменен")
        elif message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция прервана")
        else:
            msg = bot.send_message(message.from_user.id, "⚙ ID должен быть цифрой (для отмены No):")
            bot.register_next_step_handler(msg, lambda m: investor(m, status))

    @bot.message_handler(func=lambda message: message.text == names.MAILING)
    @valid_user(bot)
    def mailing(message):
        user_btn = tb.types.ReplyKeyboardMarkup(True)
        user_btn.row(names.FOR_ONE, names.FOR_INVEST)
        user_btn.row(names.FOR_PERF, names.FOR_UN_PERF)
        user_btn.row(names.BACK)
        bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    @bot.message_handler(func=lambda message: message.text == names.MAIL_BACK)
    @valid_user(bot)
    def mail_back(message):
        admin_menu(message)

    @bot.message_handler(
        func=lambda message: message.text in [names.FOR_ONE, names.FOR_INVEST, names.FOR_PERF, names.FOR_UN_PERF])
    @valid_user(bot)
    def change_mail(message):
        if message.text == names.FOR_ONE:
            call_data_mail, call_data_poll = names.FOR_ONE_MAIL, names.FOR_ONE_POLL
        elif message.text == names.FOR_INVEST:
            call_data_mail, call_data_poll = names.FOR_INVEST_MAIL, names.FOR_INVEST_POLL
        elif message.text == names.FOR_PERF:
            call_data_mail, call_data_poll = names.FOR_PERF_MAIL, names.FOR_PERF_POLL
        else:
            call_data_mail, call_data_poll = names.FOR_UN_PERF_MAIL, names.FOR_UN_PERF_POLL

        keyboard = tb.types.InlineKeyboardMarkup()
        send_mail = tb.types.InlineKeyboardButton(text=names.SEND_MAIL, callback_data=call_data_mail)
        send_poll = tb.types.InlineKeyboardButton(text=names.SEND_POLL, callback_data=call_data_poll)

        keyboard.row(send_mail, send_poll)

        bot.send_message(message.from_user.id, message.text, disable_notification=True, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == names.FOR_ONE_MAIL or call.data == names.FOR_ONE_POLL)
    @valid_user(bot)
    def send_one(call):
        msg = bot.send_message(
            call.from_user.id, "⚙ Укажите ID(цифра) пользователя, которому отправить сообщение (для отмены No): ")
        bot.register_next_step_handler(msg, lambda m: to_send(m, call.data))

    def to_send(message, call_data):
        if is_number(message.text):
            user_info_by_id = db.get_user_id_by_id(message.text)

            if len(user_info_by_id) == 0:
                bot.send_message(message.from_user.id, "⚙ Пользователь с таким ID не найден, (для отмены No):")

                bot.register_next_step_handler(message, lambda m: to_send(m, call_data))
            else:
                if call_data == names.FOR_ONE_MAIL:
                    mail_text(message, message.text)
                else:
                    poll_text(message, message.text)
        elif message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция прервана")
        else:
            msg = bot.send_message(message.from_user.id, "⚙ ID должен быть цифрой (для отмены No):")
            bot.register_next_step_handler(msg, lambda m: to_send(m, call_data))

    @bot.callback_query_handler(func=lambda call: call.data in [
        names.FOR_INVEST_MAIL,
        names.FOR_PERF_MAIL,
        names.FOR_UN_PERF_MAIL
    ])
    def mail_text(call, call_data=None):
        call_data = call.data[0:-4] if not call_data else call_data
        msg = bot.send_message(call.from_user.id, "⚙ Введите текст сообщения: (для отмены No): ")
        bot.register_next_step_handler(msg, lambda m: is_mail_text(m, call_data))

    def is_mail_text(message, call_data):
        if message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция прервана")
        else:
            keyboard = tb.types.InlineKeyboardMarkup()
            send_button = tb.types.InlineKeyboardButton(text='Отправить', callback_data=call_data)
            keyboard.add(send_button)

            bot.send_message(message.from_user.id, message.text, disable_notification=True, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data in [
        names.FOR_INVEST_POLL,
        names.FOR_PERF_POLL,
        names.FOR_UN_PERF_POLL
    ])
    def poll_text(call, call_data=None):
        call_data = call.data[0:-4] if not call_data else call_data
        msg = bot.send_message(call.from_user.id, "⚙ Введите вопрос голосования: (для отмены No): ")
        bot.register_next_step_handler(msg, lambda m: is_poll_text(m, call_data))

    def is_poll_text(message, call_data):
        if message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция прервана")
        elif message.content_type == 'text':
            poll = tb.types.Poll(message.text)
            msg = bot.send_message(message.from_user.id, "⚙ Введите вариант ответа (для отмены No, отправить Send): ")
            bot.register_next_step_handler(msg, lambda m: poll_options(m, call_data, poll))
        else:
            msg = bot.send_message(message.from_user.id, "⚙ Вопрос должен быть текстом, повторите ввод: "
                                                         "(для отмены No, отправить Send): ")
            bot.register_next_step_handler(msg, lambda m: is_poll_text(m, call_data))

    def poll_options(message, call_data, poll):
        if message.text == "No":
            bot.send_message(message.from_user.id, "⚙ Операция прервана")
        elif message.text == 'Send':
            if len(poll.options) >= 2:
                keyboard = tb.types.InlineKeyboardMarkup()
                send_button = tb.types.InlineKeyboardButton(text='Отправить', callback_data=call_data)
                keyboard.add(send_button)

                bot.send_poll(message.from_user.id, poll=poll, reply_markup=keyboard)
            else:
                msg = bot.send_message(message.from_user.id, "⚙ Вариантов не может быть менее 2-ух, добавте варинат: "
                                                             "(для отмены No, отправить Send): ")
                bot.register_next_step_handler(msg, lambda m: poll_options(m, call_data, poll))
        elif message.content_type == 'text':
            poll.add(message.text)
            msg = bot.send_message(message.from_user.id, "⚙ Введите вариант ответа (для отмены No, отправить Send): ")
            bot.register_next_step_handler(msg, lambda m: poll_options(m, call_data, poll))
        else:
            msg = bot.send_message(message.from_user.id, "⚙ Вариант ответа должен быть текстом, повторите ввод: "
                                                         "(для отмены No, отправить Send): ")
            bot.register_next_step_handler(msg, lambda m: poll_options(m, call_data, poll))

    def complete_mail(call, users_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)

        for user in users_id:
            try:
                bot.send_message(user, call.message.text)
            except:
                pass
        bot.send_message(call.from_user.id, '📬 Сообщения отправлены!')

    def complete_poll(call, users_id):
        for user in users_id:
            try:
                bot.forward_message(user, call.from_user.id, call.message.message_id)
            except:
                pass
        bot.forward_message(call.from_user.id, call.from_user.id, call.message.message_id)

        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.from_user.id, '📬 Голосования отправлены! Используйте сообщение выше, для отслеживания результата.')

    @bot.callback_query_handler(func=lambda call: is_number(call.data))
    @valid_user(bot)
    def mailing_one(call):
        users_id = db.get_user_id_by_id(call.data)
        complete_poll(call, users_id) if call.message.content_type == 'poll' else complete_mail(call, users_id)

    @bot.callback_query_handler(func=lambda call: call.data == names.FOR_INVEST_CALL)
    @valid_user(bot)
    def mailing_invest(call):
        users_id = db.get_investor_id(1)
        complete_poll(call, users_id) if call.message.content_type == 'poll' else complete_mail(call, users_id)

    @bot.callback_query_handler(func=lambda call: call.data == names.FOR_PERF_CALL)
    @valid_user(bot)
    def mailing_perf(call):
        users_id = db.get_valid_id(1)
        complete_poll(call, users_id) if call.message.content_type == 'poll' else complete_mail(call, users_id)

    @bot.callback_query_handler(func=lambda call: call.data == names.FOR_UN_PERF_CALL)
    @valid_user(bot)
    def mailing_un_perf(call):
        users_id = db.get_valid_id(0)
        complete_poll(call, users_id) if call.message.content_type == 'poll' else complete_mail(call, users_id)

    return bot


def main():
    api_token = "token"
    bot = create_bot(api_token)
    schedule.every().day.at("00:01").do(daily_bonus)
    thread = Thread(target=schedule_start)
    thread.start()
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except:
            handle = open("./loggs.txt", "w")
            handle.write(f'Ошибка:\n{traceback.format_exc()}\n')
            handle.close()
            time.sleep(15)


if __name__ == '__main__':
    main()
