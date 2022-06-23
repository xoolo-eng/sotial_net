import pathlib
import os
from .__file_logging import LOG_CONFIG

BASE_DIR = pathlib.Path(__file__).parent.parent.absolute()

DEBUG = True
ACTIVATE_TIME = 60 * 60 * 24
TASKS_INTERVAL = 60 * 60
EXPIRE_TIME = 120 * 120

DATABASE = {
    "connections": {"default": "sqlite://{}".format(BASE_DIR / "snet.sqlite")},
    # TODO: при старте забирать инфу из пакета
    "apps": {
        "user": {
            "models": ["snet.web.user.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}
EMAIL = {
    "sender": "info@sotial_net.com",
    "hostname": "smtp.gmail.com",
    "port": 587,
    "start_tls": True,
    "username": "d.a.xolloo@gmail.com",
    "password": os.getenv("EMAIL_PASS"),
}


LOGGER = "snet.prod"
EXC_LOGGER = "snet.except"
if DEBUG:
    LOGGER = "snet.dev"
