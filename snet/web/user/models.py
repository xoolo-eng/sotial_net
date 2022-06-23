import asyncio
import aiosmtplib
import pytz
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tortoise import models, fields
from tortoise.signals import pre_save, post_save
from hashlib import sha3_256, sha3_512
from datetime import datetime, timedelta
from random import randrange
from snet.app.utils import CryptoField, MemCache, Log
from snet.conf import settings


class User(models.Model):
    # TODO: check username
    id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=120, unique=True)
    created = fields.DatetimeField(auto_now_add=True)
    last_login = fields.DatetimeField(auto_now=True)
    password = CryptoField()
    is_active = fields.BooleanField(default=False)
    birth_day = fields.DateField()
    bio = fields.TextField()
    avatar = fields.TextField()
    friends = fields.ManyToManyField(
        "user.User",
        related_name="followers",
        on_delete=fields.SET_NULL,
    )
    refresh = fields.TextField(null=True)

    class Meta:
        table = "users"

    def set_password(self):
        salt = self.username + str(randrange(1000000, 9999999))
        salt = sha3_256(salt.encode("utf-8")).hexdigest()
        tmp = sha3_256(self.password.encode("utf-8")).hexdigest()
        data = "".join([s + t for s, t in zip(salt, tmp)])
        self.password = sha3_512(data.encode("utf-8")).hexdigest() + salt

    async def check_password(self, password):
        salt = self.password[-64:]
        tmp = sha3_256(password.encode("utf-8")).hexdigest()
        data = "".join([s + t for s, t in zip(salt, tmp)])
        hashed_pass = sha3_512(data.encode("utf-8")).hexdigest()
        if hashed_pass == self.password[:-64]:
            return True
        await asyncio.sleep(3)
        return False

@pre_save(User)
async def to_hash_password(sender, instance, using_db, update_fields):
    if (update_fields is None) or ("password" in update_fields):
        instance.set_password()

@post_save(User)
async def send_activation_email(sender, instance, created, using_db, update_fields):
    if created:
        user_code = sha3_256(instance.username.encode("utf-8")).hexdigest()
        async with MemCache() as redis:
            await redis.set(user_code, instance.username, ex=settings.ACTIVATE_TIME)
        link = "http://127.0.0.1:8080/user/activate/{}".format(user_code)
        print(link)
        if not settings.DEBUG:
            message = MIMEMultipart("alternative")
            message["From"] = "info@sotial_net.com"
            message["To"] = instance.email
            message["Subject"] = "Activate account for {}.".format(instance.username)
            message.attach(MIMEText("Activate link: {}".format(link), "plan", "utf-8"))
            message.attach(MIMEText('<a href="{}">Activate link</a>'.format(link), "html", "utf-8"))
            await aiosmtplib.send(message, recipients=[instance.email], **settings.EMAIL)


@dataclass(frozen=True)
class AnonymousUser:
    username: str = "anonymous"


class UserCleaner(Log):
    def __init__(self, interval: int):
        self._interval = interval
        self._is_work = True
        self._task_event = asyncio.Event()

    async def __call__(self, app):
        task = asyncio.create_task(self._executor(), name=self.__class__.__name__)
        yield
        self._is_work = False
        self._task_event.set()
        await task

    async def _executor(self):
        loop = asyncio.get_running_loop()
        while self._is_work:
            loop.call_later(self._interval, lambda event: event.set(), self._task_event)
            await self._task_event.wait()
            try:
                await self._handler()
            except Exception as err:
                self.log.error(err)
                self.exc_log.error(self.trace)
            finally:
                self._task_event.clear()

    @staticmethod
    async def _handler():
        users = await User.filter(is_active=False)
        for user in users:
            if (user.created + timedelta(seconds=settings.ACTIVATE_TIME)).replace(
                tzinfo=pytz.UTC
            ) < datetime.now().replace(tzinfo=pytz.UTC):
                await user.delete()
                print("User", user.username, "was deleted")
