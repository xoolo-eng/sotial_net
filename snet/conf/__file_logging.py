import logging.handlers
import os
import pathlib


LOG_DIR = pathlib.Path(os.getenv("LOG_DIR"))

if not LOG_DIR.exists():
    if LOG_DIR.is_absolute():
        LOG_DIR.mkdir(parents=True)
    else:
        raise ValueError(f"LOG_DIR '{LOG_DIR}' is not absolute path.")


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[%(asctime)s] # LINE: %(lineno)-5d %(filename)s %(message)s."},
        "hard": {"format": "[%(asctime)s | %(levelname)s] %(pathname)s # LINE: %(lineno)-5d %(filename)s %(message)s"},
        "exception": {
            "format": "[%(asctime)s | %(levelname)s] %(pathname)s # LINE: %(lineno)-5d %(filename)s\n%(message)s"
        },
        "json": {"format": '{"level": "%(levelname)s", "time": "%(asctime)s", "message": "%(message)s"}'},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": LOG_DIR / "social_net.log",
            "maxBytes": 2 ** 16,
            "backupCount": 4,
            "encoding": "utf-8",
        },
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "formatter": "hard",
            "address": "/dev/log",
            "facility": "local0",
        },
        "exc_console": {
            "class": "logging.StreamHandler",
            "formatter": "exception",
            "stream": "ext://sys.stdout",
        },
        "exc_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "exception",
            "filename": LOG_DIR / "exceptions.log",
            "maxBytes": 2 ** 16,
            "backupCount": 8,
            "encoding": "utf-8",
        },
        "exc_syslog": {
            "class": "logging.handlers.SysLogHandler",
            "formatter": "exception",
            "address": "/dev/log",
            "facility": "local1",
        },
    },
    "loggers": {
        "snet.dev": {"level": "DEBUG", "handlers": ["console", "file", "syslog"]},
        "snet.prod": {"level": "INFO", "handlers": ["file", "syslog"]},
        "snet.except": {"level": "ERROR", "handlers": ["exc_console", "exc_syslog", "exc_file"]},
    },
}
