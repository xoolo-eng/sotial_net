from aiohttp import web


# async def start(app):
#     app["connections"].extend([1, 2, 3, 4])
#
#
# async def shutdown(app):
#     for i in app["connections"]:
#         print(i)
#
#
# async def start_stop(app):
#     print("START")
#     yield
#     print("STOP")


def create_app():
    app = web.Application()
    # app.on_startup.extend([start])
    # app.on_shutdown.extend([shutdown])
    # app.cleanup_ctx.extend([start_stop])
    # app.middlewares.extend([])
    app["connections"] = []
    return app


async def get_application():
    return create_app()


def run():
    app = create_app()
    web.run_app(app, host="127.0.0.1")
