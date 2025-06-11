import asyncio

from filters import FilterExpression
from .router import Router
from .types import Message, Callback
from maxbot.bot import Bot
from typing import Callable, List

class Dispatcher:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.message_handlers: List[tuple[Callable, FilterExpression | None]] = []
        self.callback_handlers: List[tuple[Callable, FilterExpression | None]] = []
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
                        for func, flt in self.message_handlers:
                            if flt is None or flt.check(msg):
                                await func(msg)

                        for router in self.routers:
                            for func, flt in router.message_handlers:
                                if flt is None or flt.check(msg):
                                    await func(msg)


                    elif update_type == "message_callback":

                        try:

                            cb = Callback(**update["callback"])

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
                        # можешь тут вызывать специальные хендлеры

                    # обновляем offset/marker
                    marker = response.get("marker", marker)

            except Exception as e:
                print(f"[Dispatcher] Ошибка: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(1)

    def run_polling(self):
        asyncio.run(self._polling())
