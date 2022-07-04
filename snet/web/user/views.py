import jwt

# import enum
from aiohttp import web
from datetime import datetime, timedelta
from tortoise.exceptions import DoesNotExist
from snet.web.root.views import SerializeView
from snet.web.user.models import User, AnonymousUser
from snet.app.utils import MemCache, Log
from snet.conf import settings
from snet.app.permissions import SimplePermission, AnonymousPermission, AnyPermission, TokenType
from functools import partial


# class TokenType(str, enum.Enum):
#     REFRESH = "refresh"
#     ACCESS = "access"


@AnonymousPermission
class TokenCreate(web.View, Log):
    async def post(self):
        data = await self.request.json()
        try:
            user = await User.get(username=data.get("username"))
        except DoesNotExist:
            self.log.warn("user {!r} not found".format(data.get("username")))
            return web.json_response({"message": "User not found"}, status=404)
        if await user.check_password(data.get("password")):
            refresh = jwt.encode({"username": user.username, "type": TokenType.REFRESH}, "password", algorithm="HS256")
            user.refresh = refresh
            await user.save(update_fields=("refresh",))
            return web.json_response({"refresh": refresh}, status=201)
        self.log.warn("Invalid password for {!r}".format(user.username))
        return web.json_response({"message": "Invalid password"}, status=404)


class TokenView(web.View, Log):
    async def post(self):
        refresh = self.request.headers.get("Refresh")
        if refresh is None:
            ...
            return
        data = jwt.decode(refresh, "password", algorithms="HS256")
        if data.get("type") != TokenType.REFRESH:
            ...
            return
        try:
            user = await User.get(username=data.get("username"))
        except DoesNotExist:
            self.log.warn(f"""User '{data.get("username")}' not found""")
            return
        if user.refresh != refresh:
            ...
            return
        # refresh = jwt.encode({"username": user.username, "type": TokenType.REFRESH}, "password", algorithm="HS256")
        # user.refresh = refresh
        # await user.save(update_fields=("refresh",))
        access = jwt.encode(
            {
                "username": user.username,
                "type": TokenType.ACCESS,
                "refresh": refresh,
                "exp": round((datetime.now() + timedelta(seconds=settings.EXPIRE_TIME)).timestamp()),
            },
            "password",
            algorithm="HS256",
        )
        return web.json_response(
            {
                "access": access,
                # "refresh": refresh,
            },
            status=201,
        )

    async def delete(self):
        refresh = self.request.headers.get("Refresh")
        if refresh is None:
            ...
            return
        data = jwt.decode(refresh, "password", algorithms="HS256")
        if data.get("type") != TokenType.REFRESH:
            ...
            return
        try:
            user = await User.get(username=data.get("username"))
        except DoesNotExist:
            self.log.warn(f"""User '{data.get("username")}' not found""")
            return
        if user.refresh != refresh:
            ...
            return
        user.refresh = None
        await user.save(update_fields=("refresh",))
        return web.json_response(
            {"message": "success delete"},
            status=200,
        )


@SimplePermission
class UserView(SerializeView, Log):
    async def get(self):
        user = dict(self.request.user)
        del user["password"]
        return self.response(user, status=web.HTTPOk)

    @AnonymousPermission.sub_permission
    async def post(self):
        data = await self.request.json(loads=self.deserialize(User))
        self.log.critical(data)
        new_user = await User.create(**data)
        new_user = dict(new_user)
        del new_user["password"]
        return self.response(new_user, status=web.HTTPCreated)

    async def put(self):
        usr = self.request.user
        data = await self.request.json()
        fields = tuple(data.keys())
        for key, value in data.items():
            setattr(usr, key, value)
        await usr.save(update_fields=fields)
        return self.response(dict(usr), status=web.HTTPOk)

    async def delete(self):
        usr = self.request.user
        await usr.delete()
        return self.response({"message": "success deleted"}, status=web.HTTPOk)


@AnyPermission
class ActivateView(web.View, Log):
    async def get(self):
        user_code = self.request.match_info["user_code"]
        async with MemCache() as redis:
            username = await redis.get(user_code)
            await redis.delete(user_code)
        if username is not None:
            try:
                user = await User.get(username=username)
            except DoesNotExist:
                self.log.error("User not found")
                return web.Response(text="User not found", status=404)
            user.is_active = True
            await user.save(update_fields=("is_active",))
            return web.Response(text="Success")
