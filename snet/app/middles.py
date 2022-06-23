import jwt
import json
from aiohttp import web, hdrs
from tortoise.exceptions import DoesNotExist
from snet.app.utils import Log
from snet.app.utils import MemCache
from snet.web.user.models import User, AnonymousUser
from snet.app.permissions import TokenType
from functools import wraps


class ExcControl(Log):
    def __call__(self):
        @web.middleware
        async def _exc_middle(request, handler):
            try:
                return await handler(request)
            except Exception as err:
                if not isinstance(err, web.HTTPException):
                    self.log.critical(err)
                    self.exc_log.error(self.trace)
                    return web.json_response({"message": str(err)}, status=web.HTTPInternalServerError.status_code)
                return await handler(request)

        return _exc_middle


class HeaderControl(Log):
    def __call__(self):
        @web.middleware
        async def _middle(request, handler):
            self.log.debug(request.method)
            self.log.info(json.dumps([*request.headers.items()]))
            try:
                response = await handler(request)
            except Exception as err:
                self.log.error(err)
                self.exc_log.error(self.trace)
                raise
            return response

        return _middle


class JWTToken(Log):
    def middle(self):
        @web.middleware
        async def _middle(request, handler):
            if request.method in [hdrs.METH_GET, hdrs.METH_POST, hdrs.METH_PUT, hdrs.METH_DELETE]:
                auth_hdr = request.headers.get("Authorization")
                if auth_hdr is None:
                    request.user = AnonymousUser()
                    return await handler(request)
                try:
                    schema, access_token = auth_hdr.strip().split(" ")
                except ValueError:
                    self.log.warn("Invalid 'Authorization' header: ".format(request.headers.get("Authorization")))
                    return web.json_response(
                        {"message": "invalid 'Authorization' header"}, status=web.HTTPUnauthorized.status
                    )
                if schema != "Bearer":
                    return web.json_response({"message": "invalid token schema"}, status=web.HTTPUnauthorized.status)
                try:
                    token_info = jwt.decode(access_token, "password", algorithms="HS256")
                except jwt.exceptions.ExpiredSignatureError:
                    self.log.warn("Invalid token. Headers: {}".format(json.dumps([*request.headers.items()])))
                    return web.json_response({"message": "invalid token"}, status=web.HTTPUnauthorized.status_code)
                else:
                    self.log.debug(token_info)
                    if TokenType(token_info["type"]) == TokenType.REFRESH:
                        return web.json_response({"message": "invalid token"}, status=web.HTTPUnauthorized.status_code)
                try:
                    user = await User.get(username=token_info["username"])
                except DoesNotExist:
                    self.log.error("Invalid username in token: {}".format(json.dumps(token_info)))
                    return web.json_response({"message": "Permissions denied"}, status=web.HTTPForbidden.status_code)
                request.user = user
            return await handler(request)

        return _middle
