from smoservice.forum import views
from aiohttp import web
from core.handlers.Balance import crypto


# настраиваем пути, которые будут вести к нашей странице
def setup_routes(app):
    app.router.add_get("/tegroSuccess", views.index)
    app.router.add_get("/", views.index)
    app.router.add_post('/cryptobot', crypto.get_updates)
    app.router.add_post('/tonwallet', views.cryptopay)
    app.router.add_get("/tegroFail", views.tegroFail)
