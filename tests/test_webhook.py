import asyncio
import os
import sys
import types

# Provide a minimal aiohttp stub so cat_weather.main can be imported
aiohttp_stub = types.ModuleType("aiohttp")

class DummySession:
    def post(self, url, json=None):
        class Resp:
            async def __aenter__(self2):
                return self2
            async def __aexit__(self2, exc_type, exc, tb):
                pass
            def raise_for_status(self2):
                pass
            async def json(self2):
                return {}
        return Resp()
    async def close(self):
        pass

aiohttp_stub.ClientSession = DummySession
aiohttp_stub.web = types.SimpleNamespace(
    Request=object,
    Response=object,
    Application=object,
)
sys.modules.setdefault("aiohttp", aiohttp_stub)

aiogram_stub = types.ModuleType("aiogram")
aiogram_stub.Bot = object
aiogram_stub.Dispatcher = object
aiogram_stub.Router = object
aiogram_stub.F = object
aiogram_stub.filters = types.SimpleNamespace(Command=object)
aiogram_stub.types = types.SimpleNamespace(Message=object, ChatMemberUpdated=object)
sys.modules.setdefault("aiogram", aiogram_stub)

os.environ.setdefault("WEBHOOK_URL", "https://test.local")

from cat_weather.main import ensure_webhook



class DummyBot:
    def __init__(self, url=""):
        self.url = url
        self.calls = []

    async def api_request(self, method: str, data=None):
        self.calls.append((method, data))
        if method == "getWebhookInfo":
            return {"result": {"url": self.url}}
        if method == "setWebhook":
            self.url = data["url"]
            return {"ok": True}
        raise NotImplementedError(method)



def test_ensure_webhook_registers_when_missing():
    bot = DummyBot()
    asyncio.run(ensure_webhook(bot, "https://example.com"))
    assert bot.url == "https://example.com/webhook"

    assert ("setWebhook", {"url": "https://example.com/webhook"}) in bot.calls



def test_ensure_webhook_no_change():
    bot = DummyBot("https://example.com/webhook")
    asyncio.run(ensure_webhook(bot, "https://example.com"))
    assert bot.url == "https://example.com/webhook"
    assert len(bot.calls) == 1
