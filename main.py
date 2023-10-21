import logging
import sys
import asyncio
from os import getenv
from finite_state_machine import form_router
from dotenv import load_dotenv
from core.handlers import StartCommand, SendAllAdmin, ReferralLink, Parsing, ListOrders, Help, FAQ, CreateAnOrder, \
    Check, admin, AdmibGetAllOrders, AddOrRemoveCategory, Balance, CreateBot, Inline_Query, AdminGetService, \
    CheckStatus
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from aiogram.filters.state import State, StatesGroup
from aiohttp import web
import jinja2
import aiohttp_jinja2
from smoservice.forum import views

load_dotenv()
main_router = Router()
BASE_URL = getenv("BOT_URL")
MAIN_BOT_TOKEN = getenv("TOKEN")

WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 8080
MAIN_BOT_PATH = "/webhook/main"
OTHER_BOTS_PATH = "/webhook/bot/{bot_token}"
OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"
MAIN_BOT_URL = f"{BASE_URL}{MAIN_BOT_PATH}"



class FSMFillFrom(StatesGroup):
    get_bot_token = State()


def setup_routes(application):
    from smoservice.forum.routes import setup_routes as setup_forum_routes
    setup_forum_routes(application)


def setup_external_libraries(application: web.Application) -> None:
    aiohttp_jinja2.setup(application, loader=jinja2.FileSystemLoader("templates"))


def setup_app(application):
    setup_external_libraries(application)
    setup_routes(application)


async def sheduler(period, fu, *args, **kw):
    while True:
        await asyncio.sleep(period)
        await fu(*args, **kw)


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(f"{BASE_URL}{MAIN_BOT_PATH}")
    loop = asyncio.get_event_loop()  # или asyncio.get_event_loop() если уже есть запущенный луп.

    loop.create_task(sheduler(1800, CheckStatus.check_status))


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    session = AiohttpSession()
    bot_settings = {"session": session, "parse_mode": ParseMode.HTML}
    bot = Bot(token=MAIN_BOT_TOKEN, **bot_settings)
    storage = MemoryStorage()

    main_dispatcher = Dispatcher(storage=storage)
    multibot_dispatcher = Dispatcher(storage=storage)

    main_dispatcher.include_router(CreateBot.NewBotRouter)
    main_dispatcher.include_routers(StartCommand.StartRouter,
                                    admin.AdminRouter, CreateAnOrder.OrderRouter,
                                    FAQ.FAQRouter, Help.HelpRouter, Inline_Query.QueryRouter,
                                    ListOrders.ListOrders, Parsing.ParsingRouter, ReferralLink.ReferralRouter,
                                    SendAllAdmin.SendAllRouter, AdminGetService.AdminGetServiceRouter, main_router)
    main_dispatcher.include_routers(AddOrRemoveCategory.AddOrRemoveCategoryRouter, AdmibGetAllOrders.AdminAllOrders,
                                    Check.CheckRouter, Balance.BalanceRouter)
    main_dispatcher.startup.register(on_startup)

    multibot_dispatcher.include_router(form_router)

    app = web.Application()
    setup_app(app)
    SimpleRequestHandler(dispatcher=main_dispatcher, bot=bot).register(app, path=MAIN_BOT_PATH)
    TokenBasedRequestHandler(
        dispatcher=main_dispatcher,
        bot_settings=bot_settings,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, main_dispatcher, bot=bot)
    setup_application(app, multibot_dispatcher)
    app.router.add_static('/static/', path='static', name='static')
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
