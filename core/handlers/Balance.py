# Обработка баланса
import os
from aiogram.filters import StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F
from core.keyboards import Button
from core.config import config
from http.server import BaseHTTPRequestHandler
import database as db
from urllib.parse import urlencode
import uuid
import requests
import json
import time
import hmac
import hashlib
import datetime
import jinja2
from aiogram import Bot, Router
from aiogram.types.input_file import FSInputFile
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update
from walletpay import Client

# Глобальные переменные для получения и обновления баланса
global invoice
Sum = 0.0
order_id = ''
user_id = 0
crypto = AioCryptoPay(token='14148:AA9QPgvYz9GQD5osr02NNKTJBRkU4VbkFNv', network=Networks.MAIN_NET)


BalanceRouter = Router()

# Создаем FSM
class FSMFillFrom(StatesGroup):
    ReplenishBalance = State()
    GetPay = State()


# Обработка команды
@BalanceRouter.message(Command('mybalance'))
async def MyBalanceKeyboard(message: Message, state: FSMContext):
    # Вызов главное функции
    await MyBalance(message, state)


# Обработка кнопки Мой Баланс
@BalanceRouter.message(F.text == '👛 Кошелёк')
async def MyBalance(message: Message, state: FSMContext):
    # Получаем баланс из бд с помощью id
    balance = await db.GetBalance(message.from_user.id)
    text = f'Ваш баланс: {balance[0]} руб.\n' \
           '💳 Выберите действие ниже:'
    # Используем FSM
    await message.answer(text, reply_markup=Button.BalanceKeyboard)
    await state.set_state(FSMFillFrom.ReplenishBalance)


@BalanceRouter.callback_query(F.data == 'replenish_balance')
async def replenish_balance(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('💳 Введите сумму пополнения ниже или выберете из предложенных вариантов ', reply_markup=Button.BalanceSumKeyboard)
    await state.set_state(FSMFillFrom.ReplenishBalance)


# Обработка FSM для пополнения баланса
@BalanceRouter.callback_query(F.data.startswith('SumReplenish_'))
async def ReplenishBalance(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    global Sum, order_id, user_id, invoice
    Info = await bot.get_me()
    Sum = int(call.data[13:])
    user_id = call.from_user.id
    Shopped = str(os.getenv('SHOPID'))
    SecretKey = str(os.getenv('SECRETKEY'))
    order_id = uuid.uuid4()
    data = {
        'shop_id': Shopped,
        'amount': Sum,
        'currency': 'RUB',
        'order_id': order_id,
    }
    sorted_data = sorted(data.items())
    data_string = urlencode(sorted_data)
    sign = hashlib.md5((data_string + SecretKey).encode()).hexdigest()
    PayUrl = f'https://tegro.money/pay/?{data_string}&receipt[items][0][name]=Replenish&receipt[items][0][count]=1&receipt[items][0][price]={Sum}&sign={sign}'

    sum_ton = Sum / config.TON
    invoice = await crypto.create_invoice(asset='TON', amount=sum_ton)

    await call.message.answer('Выберите способ оплаты', reply_markup=await Button.TegroPay(PayUrl, invoice.pay_url))
    await call.message.delete()


@BalanceRouter.message(StateFilter(FSMFillFrom.ReplenishBalance))
async def ReplenishBalance(message: Message, state: FSMContext, bot: Bot):
    global Sum, order_id, user_id, invoice
    Info = await bot.get_me()
    if message.text.isdigit() is True:
        Sum = float(message.text)
        user_id = message.from_user.id
        Shopped = str(os.getenv('SHOPID'))
        SecretKey = str(os.getenv('SECRETKEY'))
        order_id = uuid.uuid4()
        data = {
            'amount': int(Sum),
            'currency': 'RUB',
            'order_id': order_id,
            'shop_id': Shopped,
        }
        sorted_data = sorted(data.items())
        data_sign = urlencode(sorted_data)
        print(data_sign)
        sign = hashlib.md5((data_sign + SecretKey).encode()).hexdigest()
        PayUrl = f'https://tegro.money/pay/?{data_sign}&receipt[items][0][name]=Replenish&receipt[items][0][count]=1&receipt[items][0][price]={Sum}&sign={sign}'
        print(PayUrl)


        sum_ton = Sum/config.TON
        invoice = await crypto.create_invoice(asset='TON', amount=sum_ton)


        headers = {
            'Wpay-Store-Api-Key': '3Qkdyg4P12UuGXTBc199kEd21o8mv3KxNt4A',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        payload = {
            'amount': {
                'amount': Sum,
                'currencyCode': 'RUB',  # выставляем счет в долларах США
            },
            'description': 'Goods and service.',
            'externalId': f'{order_id}',  # ID счета на оплату в вашем боте
            'timeoutSeconds': 60 * 60 * 24,  # время действия счета в секундах
            'customerTelegramUserId': f'{message.from_user.id}',  # ID аккаунта Telegram покупателя
            'returnUrl': f'https://t.me/{Info.username}',  # после успешной оплаты направить покупателя в наш бот
            'failReturnUrl': 'https://t.me/wallet',  # при отсутствии оплаты оставить покупателя в @wallet
        }

        response = requests.post(
            "https://pay.wallet.tg/wpay/store-api/v1/order",
            json=payload, headers=headers, timeout=10
        )
        data = response.json()

        await message.answer('Выберите способ оплаты', reply_markup=await Button.TegroPay(PayUrl, invoice.pay_url))
    else:
        await state.clear()


@BalanceRouter.callback_query(F.data == 'history_balance')
async def history_balance(callback: CallbackQuery, state: FSMContext):
    Datas = await db.Get_History(callback.from_user.id)
    TextAnswer = ''
    date = ''
    Id = 0
    if Datas:
        for data in Datas:
            if data[0] > Id:
                Id = data[0]
                date = data[4]
                month = data[4].split('-')
                TextAnswer = f'<b>• {month[2]}.{month[1]}.{month[0]}</b>\n'
        for data in Datas:
            if data[4] == date:
                Time = data[5].split(':')
                if data[2] > 0:
                    TextAnswer += f'<i>{Time[0]}:{Time[1]} {data[3]} +{data[2]} рублей</i>\n'
                else:
                    TextAnswer += f'<i>{Time[0]}:{Time[1]} {data[3]} {data[2]} рублей</i>\n'
        await callback.message.answer(TextAnswer, reply_markup=Button.GetAllHistoryKeyboard)
        await callback.message.delete()
    else:
        TextAnswer = 'У вас нет операций по счету'
        await callback.answer(TextAnswer)


@BalanceRouter.callback_query(F.data == 'Get_All_History')
async def Get_All_History(callback: CallbackQuery, state: FSMContext, bot: Bot):
    Datas = await db.Get_History(callback.from_user.id)
    file = open(f"отчет_{callback.from_user.id}.txt", "w+")
    date = ''
    for data in Datas:
        if date != data[4]:
            date = data[4]
            day = date.split('-')[2]
            month = date.split('-')[1]
            year = date.split('-')[0]
            file.write(f"{day}.{month}.{year}\n")
        hour = data[5].split(':')[0]
        minute = data[5].split(':')[1]
        file.write(f"{hour}:{minute} {data[3]} {data[2]} рублей\n")
    file.close()
    document = FSInputFile(f'отчет_{callback.from_user.id}.txt')
    await bot.send_document(callback.from_user.id, document)
    await callback.message.delete()


async def tegro_success(request):
    param2 = request.query.get('status')
    bot = Bot(token=os.getenv('TOKEN'))
    if param2 == 'success':
        await db.UpdateBalance(user_id, Sum)
        await bot.send_message(chat_id=user_id, text='оплата прошла успешно', reply_markup=Button.ReplyStartKeyboard)
        await db.Add_History(user_id, Sum, 'Пополнение')


async def tegro_fail(request):
    bot = Bot(token=os.getenv('TOKEN'))
    await bot.send_message(user_id, 'оплата не прошла', reply_markup=Button.ReplyStartKeyboard)


@crypto.pay_handler()
async def invoice_paid(update: Update, app) -> None:
    bot = Bot(token=os.getenv('TOKEN'))
    if update.payload.status == 'paid':
        await db.UpdateBalance(user_id, Sum)
        await bot.send_message(chat_id=user_id, text='оплата прошла успешно', reply_markup=Button.ReplyStartKeyboard)
        await db.Add_History(user_id, Sum, 'Пополнение')


async def ton_wallet_success(request):
    bot = Bot(token=os.getenv('TOKEN'))
    for event in request.get_json():
        if event["type"] == "ORDER_PAID":
            data = event["payload"]
            print("Оплачен счет N {} на сумму {} {}. Оплата {} {}.".format(
                data["externalId"],  # ID счета в вашем боте, который мы указывали при создании ссылки для оплаты
                data["orderAmount"]["amount"],  # Сумма счета, указанная при создании ссылки для оплаты
                data["orderAmount"]["currencyCode"],  # Валюта счета
                data["selectedPaymentOption"]["amount"]["amount"],  # Сколько оплатил покупатель
                data["selectedPaymentOption"]["amount"]["currencyCode"]  # В какой криптовалюте
            ))
            await db.UpdateBalance(user_id, Sum)
            await bot.send_message(chat_id=user_id, text='оплата прошла успешно',
                                   reply_markup=Button.ReplyStartKeyboard)
            await db.Add_History(user_id, Sum, 'Пополнение')