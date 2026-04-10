import asyncio

from .fsm import FSMStorage
from .filters import FilterExpression
from .router import Router
from .types import Message, Callback
from maxbot.bot import Bot
from typing import Callable, List

from contextvars import ContextVar


class Dispatcher:
    def __init__(self, bot: Bot, workers: int = 10, max_tasks: int = 100):
        self.bot = bot
        self.storage = FSMStorage()

        self.message_handlers: List[tuple[Callable, FilterExpression | None]] = []
        self.callback_handlers: List[tuple[Callable, FilterExpression | None]] = []
        self.bot_started_handlers = []
        self.routers: list[Router] = []

        # 🔥 Новое
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_tasks)
        self.workers_count = workers

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

    # ------------------------
    # SAFE EXECUTION
    # ------------------------
    async def _safe_handle(self, func, event):
        async with self.semaphore:
            try:
                await func(event)
            except Exception as e:
                print(f"[Handler ERROR] {func.__name__}: {e}")

    # ------------------------
    # PROCESS UPDATE
    # ------------------------
    async def _process_update(self, update: dict):
        update_type = update.get("update_type")

        try:
            if update_type == "message_created":
                msg = Message.from_raw(update["message"])
                set_current_dispatcher(self)

                for func, flt in self.message_handlers:
                    if flt is None or flt.check(msg):
                        asyncio.create_task(self._safe_handle(func, msg))

                for router in self.routers:
                    for func, flt in router.message_handlers:
                        if flt is None or flt.check(msg):
                            asyncio.create_task(self._safe_handle(func, msg))

            elif update_type == "message_callback":
                cb = Callback(
                    **update["callback"],
                    message=Message.from_raw(update["message"])
                )
                set_current_dispatcher(self)

                for func, flt in self.callback_handlers:
                    if flt is None or flt.check(cb):
                        asyncio.create_task(self._safe_handle(func, cb))

                for router in self.routers:
                    for func, flt in router.callback_handlers:
                        if flt is None or flt.check(cb):
                            asyncio.create_task(self._safe_handle(func, cb))

            elif update_type == "bot_started":
                print("🚀 Бот запущен новым пользователем!")
                set_current_dispatcher(self)

                for func in self.bot_started_handlers:
                    asyncio.create_task(self._safe_handle(func, update))

                for router in self.routers:
                    for func in router.bot_started_handlers:
                        asyncio.create_task(self._safe_handle(func, update))

        except Exception as e:
            print(f"[Dispatcher] Ошибка обработки update: {e}")
            print(update)

    # ------------------------
    # WORKER
    # ------------------------
    async def worker(self):
        while True:
            update = await self.queue.get()
            await self._process_update(update)
            self.queue.task_done()

    # ------------------------
    # POLLING
    # ------------------------
    async def _polling(self):
        marker = 0

        while True:
            try:
                response = await self.bot._request(
                    "GET",
                    "/updates",
                    params={
                        "offset": marker,
                    }
                )

                updates = response.get("updates", [])

                if updates:
                    for update in updates:
                        await self.queue.put(update)

                marker = response.get("marker", marker)

                # 🔥 защита от перегрузки
                if self.queue.qsize() > 1000:
                    print(f"⚠️ Очередь перегружена: {self.queue.qsize()}")

                # 🔥 динамический sleep
                if not updates:
                    await asyncio.sleep(0.2)

            except Exception as e:
                print(f"[Dispatcher] Ошибка polling: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

    # ------------------------
    # RUN
    # ------------------------
    async def run_polling(self):
        try:
            me = await self.bot.get_me()
            print(me)
            print(f"🤖 Bot: {me.get('username', me)} | ID: {me.get('id', '-')}")
        except Exception as e:
            print("❌ Ошибка при получении информации о боте:", e)
            return

        # 🔥 запускаем воркеры
        for _ in range(self.workers_count):
            asyncio.create_task(self.worker())

        # 🔥 запускаем polling
        await self._polling()


# ------------------------
# CONTEXT
# ------------------------
_current_dispatcher: ContextVar["Dispatcher"] = ContextVar("_current_dispatcher", default=None)


def get_current_dispatcher() -> "Dispatcher":
    dispatcher = _current_dispatcher.get()
    if dispatcher is None:
        raise RuntimeError("Dispatcher not set in context")
    return dispatcher


def set_current_dispatcher(dispatcher: "Dispatcher"):
    _current_dispatcher.set(dispatcher)
