import jinja2
import aiohttp_jinja2
import logging
import logging.config as lconf
from aiohttp import web
from tortoise.contrib.aiohttp import register_tortoise
from controller import controller_setup
from snet.conf import settings
from snet.app.utils import Crypto
from snet.web.user.models import UserCleaner
from snet.app.middles import ExcControl, HeaderControl, JWTToken


def create_app():
    lconf.dictConfig(settings.LOG_CONFIG)
    app = web.Application()
    app.middlewares.extend([ExcControl()(), HeaderControl()(), JWTToken().middle()])
    register_tortoise(app, config=settings.DATABASE, generate_schemas=True)
    Crypto.load_key(settings.BASE_DIR.parent / "private_key.pem")
    app.cleanup_ctx.extend([UserCleaner(settings.TASKS_INTERVAL)])
    # aiohttp_jinja2.setup(
    #     app,
    #     loader=jinja2.FileSystemLoader(
    #         [
    #             path / "templates"
    #             for path in (settings.BASE_DIR / "web").iterdir()
    #             if path.is_dir() and (path / "templates").exists()
    #         ]
    #     ),
    # )
    controller_setup(app, "snet.web.root.urls", cors=True)
    return app


async def get_application():
    return create_app()


def run():
    app = create_app()
    log = logging.getLogger(settings.LOGGER)
    log.info("Start Server")
    web.run_app(app, host="127.0.0.1")
    log.info("Stop Server")


"""gunicorn snet.app.server:get_application --bind localhost:8080 --worker-class aiohttp.GunicornUVLoopWebWorker"""
