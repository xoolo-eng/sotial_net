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
        self.model = kwargs["model"]
        del kwargs["model"]
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    # @staticmethod
    def object_hook(self, obj):
        print(self.model)
        result = {}
        for key, value in obj.items():
            try:
                int(value)
            except ValueError:
                try:
                    result[key] = parser.parse(value)
                except ValueError:
                    result[key] = value
        return result


class SerializeView(web.View):
    _serializer = ModelSerialize(indent=4)

    @staticmethod
    def deserialize(model):
        def _f(val):
            return json.loads(val, cls=ModelDeserialize, model=model)
        return _f

    def serialize(self, data: Dict | List) -> str:
        return self._serializer.encode(data)

    def response(self, data: Dict | List, status: web.HTTPException):
        return web.Response(text=self.serialize(data), status=status.status_code)
