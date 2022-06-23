import json
from datetime import datetime, date
from aiohttp import web
from typing import Union, Dict, Any, List
from tortoise.queryset import QuerySet, QuerySetSingle
from dateutil import parser


class ModelSerialize(json.JSONEncoder):
    def default(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.strftime("%c")
        if isinstance(value, date):
            return datetime.strftime(value, "%a %b %d %Y")
        return str(value)


class ModelDeserialize(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    @staticmethod
    def object_hook(obj):
        result = {}
        for key, value in obj.items():
            err = False
            try:
                result[key] = parser.parse(value)
            except ValueError:
                err = True
            else:
                err = False

            if err:
                result[key] = value
            if key == "password":
                result[key] = value
        return result


class SerializeView(web.View):
    _serializer = ModelSerialize(indent=4)

    @staticmethod
    def deserialize(val):
        return json.loads(val, cls=ModelDeserialize)

    def serialize(self, data: Dict | List) -> str:
        return self._serializer.encode(data)

    def response(self, data: Dict | List, status: web.HTTPException):
        return web.Response(text=self.serialize(data), status=status.status_code)
