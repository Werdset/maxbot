import asyncio

from .fsm import FSMStorage
from .filters import FilterExpression
from .router import Router
from .types import Message, Callback
from maxbot.bot import Bot
from typing import Callable, List

class Dispatcher:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.storage = FSMStorage()
        self.message_handlers: List[tuple[Callable, FilterExpression | None]] = []
        self.callback_handlers: List[tuple[Callable, FilterExpression | None]] = []
        self.bot_started_handlers = []
        self.routers: list[Router] = []

    def message(self, filter: FilterExpression = None):
        def decorator(func):
            self.message_handlers.append((func, filter))
            return func

        return decorator

    def include_router(self, router):
        self.routers.append(router)

    def callback(self, filter: FilterExpression = None):
        def decorator(func):
            self.callback_handlers.append((func, filter))
            return func

        return decorator

    def bot_started(self, func):
        self.bot_started_handlers.append(func)
        return func

    async def _polling(self):
        marker = 0
        while True:
            try:
                response = await self.bot._request("GET", "/updates", params={
                    "access_token": self.bot.token,
                    "offset": marker,
                })

                updates = response.get("updates", [])
                for update in updates:
                    print(f"🔔 Update: {update}")
                    update_type = update.get("update_type")

                    if update_type == "message_created":
                        msg = Message.from_raw(update["message"])
                        set_current_dispatcher(self)
                        for func, flt in self.message_handlers:
                            if flt is None or flt.check(msg):
                                await func(msg)

                        for router in self.routers:
                            for func, flt in router.message_handlers:
                                if flt is None or flt.check(msg):
                                    await func(msg)


                    elif update_type == "message_callback":

                        try:

                            cb = Callback(
                                **update["callback"],
                                message=Message.from_raw(update["message"])
                            )
                            set_current_dispatcher(self)
                            for func, flt in self.callback_handlers:
                                if flt is None or flt.check(cb):
                                    await func(cb)

                            for router in self.routers:
                                for func, flt in router.callback_handlers:
                                    if flt is None or flt.check(cb):
                                        await func(cb)

                        except Exception as e:

                            print(f"[Dispatcher] Ошибка в обработке callback: {e}")

                            print(f"[Dispatcher] Payload:\n{update}")


                    elif update_type == "bot_started":

                        print("🚀 Бот запущен новым пользователем!")

                        set_current_dispatcher(self)

                        for func in self.bot_started_handlers:
                            await func(update)

                        for router in self.routers:

                            for func in router.bot_started_handlers:
                                await func(update)

                    # обновляем offset/marker
                    marker = response.get("marker", marker)

            except Exception as e:
                print(f"[Dispatcher] Ошибка: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(0.3)

    def run_polling(self):
        asyncio.run(self._polling())


# Глобальная ссылка на активный Dispatcher
from contextvars import ContextVar

_current_dispatcher: ContextVar["Dispatcher"] = ContextVar("_current_dispatcher", default=None)

def get_current_dispatcher() -> "Dispatcher":
    dispatcher = _current_dispatcher.get()
    if dispatcher is None:
        raise RuntimeError("Dispatcher not set in context")
    return dispatcher

def set_current_dispatcher(dispatcher: "Dispatcher"):
    _current_dispatcher.set(dispatcher)