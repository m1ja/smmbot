import aiohttp_jinja2
from core.handlers import Balance
from core.handlers.Balance import crypto

# создаем функцию, которая будет отдавать html-файл
@aiohttp_jinja2.template("index.html")
async def index(request):
    await Balance.tegro_success(request)
    return {'title': 'Пишем первое приложение на aiohttp'}


@aiohttp_jinja2.template("index.html")
async def cryptopay(request):
    await Balance.ton_wallet_success(request)
    return {'title': 'Пишем первое приложение на aiohttp'}


@aiohttp_jinja2.template("index.html")
async def tegroFail(request):
    await Balance.tegro_fail(request)
    return {'title': 'Пишем первое приложение на aiohttp'}