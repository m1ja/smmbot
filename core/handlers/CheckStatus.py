import os
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F
from core.keyboards import Button
import database as db
import requests
import json
from aiogram import Bot, Router
from core.config import config


async def check_status():
    Status = await db.Orders()
    bot = Bot(token=os.getenv('TOKEN'))
    for stat in Status:
        if stat[9] != 'Completed' and stat[9] != 'Canceled' and stat[9] != 'Завершен':
            NameProduct = await db.GetProductName(stat[2])
            Service = await db.GetServiceCategory(NameProduct[1])
            key_smm = os.getenv('KEYSMMPANEL')
            if Service == 'SmmPanel':
                url = 'https://smmpanel.ru/api/v1'
                data = {
                    'key': key_smm,
                    'action': 'status',
                    'order': stat[8]
                }
                response = requests.post(url, data=data)
                OrderData = json.loads(response.text)
                Status = (OrderData['status'])
                Order_id = (OrderData['order'])
                if stat[9] != Status:
                    await db.UpdateOrderStatus(Order_id, Status)
                    await bot.send_message(stat[1], f'Статус заказа номер {stat[8]} изменен на {Status}')
            else:
                user_id_smo = os.getenv('USERIDSMOSERVICE')
                key_smo = os.getenv('KEYSMOSERVICE')
                url = 'https://smoservice.media/api/'
                data = {
                    'user_id': user_id_smo,
                    'api_key': key_smo,
                    'action': 'check_order',
                    'order_id': stat[8]
                }
                response = requests.post(url, data=data)
                OrderData = json.loads(response.text)
                Status = (OrderData['data']['status'])
                Order_id = (OrderData['data']['order_id'])
                if stat[9] != Status:
                    await db.UpdateOrderStatus(Order_id, Status)
                    await bot.send_message(stat[1], f'Статус заказа номер {stat[8]} изменен на {Status}')

    ton = requests.post('https://tegro.money/rates/TON-RUB/')
    data = json.loads(ton.text)
    rate = (data['data']['value'])
    config.TON = rate