import base64
import json
import logging
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union, Optional, TypeAlias

import aioredis
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.types import PRIVATE_KEY_TYPES, PUBLIC_KEY_TYPES
from tortoise import fields, models

from snet.conf import settings

Instance: TypeAlias = models.Model
Connect: TypeAlias = aioredis.Connection


class Crypto:
    private: PRIVATE_KEY_TYPES = None
    public: PUBLIC_KEY_TYPES = None

    @staticmethod
    def create_key(path: Path) -> str:
        private = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        with open(path / "private_key.pem", "wb") as file:
            file.write(
                private.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption("password".encode("utf-8")),
                )
            )

    @classmethod
    def load_key(cls, path: Path) -> None:
        with open(path, "rb") as file:
            cls.private = serialization.load_pem_private_key(file.read(), password="password".encode("utf-8"))
            cls.public = cls.private.public_key()

    @classmethod
    def encode(cls, value: str | bytes) -> str | bytes:
        data = cls.public.encrypt(
            value.encode("utf-8") if isinstance(value, str) else value,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            ),
        )
        return base64.b64encode(data).decode("utf-8") if isinstance(value, str) else data

    @classmethod
    def decode(cls, value: str | bytes):
        data = cls.private.decrypt(
            base64.b64decode(value) if isinstance(value, str) else value,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            ),
        )
        return data.decode("utf-8") if isinstance(value, str) else data


class CryptoField(fields.TextField):
    def __init__(self, cryptographer: Crypto = None, serialize: bool = False, **kwargs):
        self.cryptographer = cryptographer or Crypto
        self.serialize = serialize
        super().__init__(**kwargs)

    def to_db_value(self, value: Union[str, Any], instance: Instance) -> str:
        if self.serialize:
            value = json.dumps(value)
        value = super().to_db_value(value, instance)
        return self.cryptographer.encode(value)

    def to_python_value(self, value: str) -> Union[str, Any]:
        try:
            value = self.cryptographer.decode(value)
        except ValueError:
            return value
        value = super().to_python_value(value)
        if self.serialize:
            value = json.loads(value)
        return value


@dataclass
class MemCache:
    host: Optional[str] = field(default="127.0.0.1")
    port: Optional[int] = field(default=6379)
    _connection: Connect = field(init=False, default=None)

    async def __aenter__(self):
        await self.connect()
        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        self._connection = await aioredis.from_url(f"redis://{self.host}:{self.port}", decode_responses=True)

    async def close(self):
        await self._connection.close()
        self._connection = None


class Log:
    __log: logging.Logger = logging.getLogger(settings.LOGGER)
    __exc_log: logging.Logger = logging.getLogger(settings.EXC_LOGGER)

    @property
    def log(self):
        return self.__log

    @property
    def exc_log(self):
        return self.__exc_log

    @property
    def trace(self):
        return traceback.format_exc()
