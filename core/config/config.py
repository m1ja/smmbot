from aiogram import Bot, Dispatcher,Router
from dotenv import load_dotenv
import os
from aiogram import Router, F
from aiogram.enums import ChatType
import database

# Создаем бота и привязываем базу данных
load_dotenv()
Service = 'SmoService'
TON = 215
database.sql_start()
