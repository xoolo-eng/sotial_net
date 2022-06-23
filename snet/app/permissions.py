from aiohttp import web
import enum
from abc import ABC, abstractmethod
from snet.web.user.models import User, AnonymousUser


class TokenType(str, enum.Enum):
    REFRESH = "refresh"
    ACCESS = "access"


class AbstractPermission(ABC):
    def __init__(self, handler):
        self.response = {"message": "Permission denied"}
        self._handler = handler

    async def __call__(self, request):
        worker = getattr(self._handler, request.method.lower(), None)
        if worker is not None:
            perm = getattr(worker, "__permission__", None)
            if perm is not None and perm.__name__ != self.__class__.__name__:
                return await perm(self._handler)(request)
        if await self.authentication(request):
            return await self._handler(request)
        return web.json_response(self.response, status=web.HTTPForbidden.status_code)

    @classmethod
    def sub_permission(cls, func):
        func.__permission__ = cls
        return func

    @abstractmethod
    async def authentication(self, request) -> bool:
        raise NotImplementedError("Not implemented method")


class SimplePermission(AbstractPermission):
    async def authentication(self, request) -> bool:
        if isinstance(request.user, User):
            return True
        return False


class AnonymousPermission(AbstractPermission):
    async def authentication(self, request) -> bool:
        if isinstance(request.user, AnonymousUser):
            return True
        return False


class AnyPermission(AbstractPermission):
    async def authentication(self, request) -> bool:
        return True
