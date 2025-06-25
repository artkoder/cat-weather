import asyncio
import sys
import types

# Provide a minimal aiohttp stub so cat_weather.main can be imported
aiohttp_stub = types.ModuleType("aiohttp")
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

from cat_weather.main import ensure_webhook


class DummyBot:
    def __init__(self, url=""):
        self.url = url
        self.calls = []

    async def api_request(self, method: str, data=None):
        self.calls.append((method, data))
        if method == "getWebhookInfo":
            return {"url": self.url}
        if method == "setWebhook":
            self.url = data["url"]
            return True
        raise NotImplementedError


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
