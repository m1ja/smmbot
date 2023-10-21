import os
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram import F
from core.keyboards import Button
from core.config import config
import database as db
from aiogram import Bot, Router

ReferralRouter = Router()

# Обработка команды и кнопки
@ReferralRouter.message(Command('earn'))
async def ReferralLinkCommand(message: Message, bot: Bot):
    await ReferralLink(message, bot)


@ReferralRouter.message(F.text == '💰 Рефералы')
async def ReferralLink(message: Message, bot: Bot):
    # Проверяем сколько всего человек пригласил пользователей
    CountUser = await db.CountReferrals(message.from_user.id)
    MoneyUser = await db.GetMoneyReferral(message.from_user.id)
    if MoneyUser is None:
        MoneyUser = 0
    if CountUser is None:
        CountUser = 0
    Info = await bot.get_me()
    text = '🤝 Партнерская программа\n' \
           '\n' \
           '🏆 Вознаграждения по реферальной (партнерской) \n' \
           'программе разделены на два уровня:\n' \
           '├  За пользователей которые присоединились по Вашей ссылке - рефералы 1 уровня\n' \
           '└  За пользователей которые присоединились по по ссылкам Ваших рефералов - рефералы 2 уровня' \
           '\n' \
           '🤑 Сколько можно заработать?\n' \
           '├  За реферала 1 уровня: 12%\n' \
           '└  За реферала 2 уровня: 4%\n' \
           '\n' \
           '🥇 Статистика:\n' \
           f'├  Всего заработано: {MoneyUser}\n' \
           f'├  Доступно к выводу: {MoneyUser}\n' \
           f'└  Лично приглашенных: {CountUser}\n' \
           '\n' \
           '🎁 Бонус за регистрацию:\n' \
           '└  За каждого пользователя который активировал бот по вашей реферальной ссылке вы так же получаете 5 рублей.\n' \
           '\n' \
           '⤵️ Ваши ссылки:\n' \
           f'└https://t.me/{Info.username}?start=ref_{message.from_user.id}\n'
    await message.answer(text)




