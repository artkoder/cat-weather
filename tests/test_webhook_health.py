import asyncio
import os
import sys
import types

# Minimal aiohttp stub with required structures
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
                return {"ok": True}
        return Resp()
    async def close(self):
        pass

aiohttp_stub = types.ModuleType("aiohttp")
aiohttp_stub.ClientSession = DummySession

class DummyRouter:
    def add_post(self, *a, **k):
        pass
    def add_get(self, *a, **k):
        pass

class DummyApp(dict):
    def __init__(self):
        super().__init__()
        self.router = DummyRouter()
        self.on_startup = []
        self.on_cleanup = []

aiohttp_stub.web = types.SimpleNamespace(
    Application=DummyApp,
    Response=object,
    Request=object,
)

sys.modules.setdefault("aiohttp", aiohttp_stub)

# aiogram stub
aiogram_stub = types.ModuleType("aiogram")
class DummyDispatcher(dict):
    def include_router(self, router):
        pass
    async def feed_webhook_update(self, bot, data):
        pass

aiogram_stub.Dispatcher = DummyDispatcher
aiogram_stub.Router = object
aiogram_stub.F = object
filters_mod = types.ModuleType("aiogram.filters")
filters_mod.Command = object
types_mod = types.ModuleType("aiogram.types")
types_mod.Message = object
types_mod.ChatMemberUpdated = object
aiogram_stub.filters = filters_mod
aiogram_stub.types = types_mod
sys.modules.setdefault("aiogram.filters", filters_mod)
sys.modules.setdefault("aiogram.types", types_mod)
sys.modules.setdefault("aiogram", aiogram_stub)

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "token")
os.environ.setdefault("WEBHOOK_URL", "https://test.local")

import cat_weather.main as main

main.Dispatcher = DummyDispatcher
create_app = main.create_app
# Override aiohttp web classes in already imported module
main.web.Application = DummyApp
main.web.Response = object
main.web.Request = object

# Stub handler modules to avoid Router dependency
channels_stub = types.SimpleNamespace(router=object)
tz_stub = types.SimpleNamespace(router=object)
sys.modules['cat_weather.handlers.channels'] = channels_stub
sys.modules['cat_weather.handlers.tz'] = tz_stub


def test_app_startup():
    app = create_app()

    async def run():
        for cb in app.on_startup:
            await cb(app)
        for cb in app.on_cleanup:
            await cb(app)
    asyncio.run(run())
