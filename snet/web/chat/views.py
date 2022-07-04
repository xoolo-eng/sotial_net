import asyncio
from aiohttp import web
from aiohttp_jinja2 import template


async def resp(ws: web.WebSocketResponse):
    await asyncio.sleep(5)
    await ws.send_json({"message":"New message"})


class ChatPageView(web.View):
    @template("chat_page.html")
    async def get(self):
        return {}

    async def post(self):
        data = await self.request.json()
        print(data)
        return web.json_response(data, status=201)


class ChatView(web.View):
    async def get(self):
        chat_id = self.request.match_info["chat_id"]
        if chat_id != "1234567890123456":
            return web.json_response({"message": "Chat not found"}, status=404)
        ws = web.WebSocketResponse(autoping=True, heartbeat=10)
        await ws.prepare(self.request)
        async for msg in ws:
            message = msg.json()
            print(message)
            task = asyncio.gather(resp(ws))
        try:
            return ws
        finally:
            await task
