# maxbot

Асинхронный Python-фреймворк для создания ботов в мессенджере [MAX](https://max.ru).

🎯 Синтаксис как у `aiogram`  
🚀 Поддержка polling  
💬 Inline-кнопки  
📦 Простая отправка сообщений

## Установка

```bash
pip install umaxbot
```

## Пример

```python
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

bot = Bot("YourToken")
dp = Dispatcher(bot)

@dp.message()
async def on_message(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👋 Поздороваться", callback_data="hello")]
    ])
    await bot.send_message(
        chat_id = message.sender.id,
        text="Привет! Нажми на кнопку ниже:",
        notify=True,
        reply_markup=keyboard,
        format="markdown"
    )

@dp.callback()
async def on_callback(cb):
    if cb.payload == "hello":
        await bot.send_message(cb.user.id, "Приятно познакомиться!")

```