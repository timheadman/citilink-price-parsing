import json
import sched
import sys
import time

import mysql.connector as mariadb
import requests
import telebot
from bs4 import BeautifulSoup
from mysql.connector import Error

from secrets import *


# import logging - зазобраться

def open_db_connection():
    try:
        connection = mariadb.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            database=DATABASE,
        )
    except Error as e:
        print(f'Error connecting to MariaDB Platform: {e}')
        sys.exit(1)
    return connection


def add_name_to_db(connection, sku, name):
    cursor = connection.cursor(buffered=True)

    try:
        cursor.execute(
            'UPDATE urls SET name = %s WHERE sku_id = %s',
            (name, sku))
    except Error as e:
        print(f'Error: {e}')

    connection.commit()
    print(f'Updated ID: {sku}')


def add_price_to_db(connection, sku, price):
    cursor = connection.cursor(buffered=True)
    try:
        cursor.execute(
            'INSERT INTO price (sku_id, price) VALUES (%s, %s)',
            (sku, price))
    except Error as e:
        print(f'Error: {e}')

    connection.commit()
    print(f'Last Inserted ID: {cursor.lastrowid}')


def get_urls_from_db(connection):
    cursor = connection.cursor(buffered=True)
    cursor.execute('SELECT * FROM sku')
    urls = []
    for url in cursor:
        urls.append(url[2])
        if not url[1]:
            name = parsing_citilink(url[2])['name']
            add_name_to_db(connection, url[0], name)
    return urls


def get_price_from_db(connection, sku):
    cursor = connection.cursor(buffered=True)
    cursor.execute(
        'SELECT price FROM price WHERE sku_id=%s '
        'ORDER BY id DESC LIMIT 1',
        (sku,))
    for price in cursor:
        return price[0]
    else:
        return 0


def parsing_citilink(url):
    page = requests.get(url)
    print(page.status_code, end=': ')

    soup = BeautifulSoup(page.text, 'html.parser')
    data = json.loads(soup.find('script', type='application/ld+json').text)
    price = int(data['offers']['price'])
    sku = int(data['sku'])
    print(sku, price, end='')
    return {'sku': sku, 'price': price, 'name': data['name']}


def sched_citilink():
    connection = open_db_connection()
    s.enter(3600, 1, sched_citilink)
    print(time.ctime())
    urls = get_urls_from_db(connection)
    for url in urls:
        data = parsing_citilink(url)
        last_price = get_price_from_db(connection, data['sku'])
        print(f' ({last_price}) -> ', end='')
        if data['price'] != last_price and data['price'] != 0:
            add_price_to_db(connection, data['sku'], data['price'])
            bot.send_message(TELEGRAM_ADMIN_ID,
                             f"Citilink:\nИзменение стоимости {data['name']}, "
                             f"{data['sku']}:\n{last_price}р. -> {data['price']}р.")
        else:
            print('Price is the same or products out of stock.')

    connection.close()


if __name__ == '__main__':
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    s = sched.scheduler(time.time, time.sleep)
    sched_citilink()
    s.run()

# Протестировать:
# SELECT * FROM sku LEFT JOIN price ON price.sku_id = sku.id
# Добавить вывод в телеграм не sku, а name.
