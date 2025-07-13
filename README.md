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


Основные возможности
Отправка, редактирование и удаление сообщений

Передача файлов (фото, аудио, видео, документы)

Работа с инлайн-клавиатурой (InlineKeyboardMarkup)

Удобный доступ к медиа через объекты Attachment

FSM — хранение состояния пользователя, data, reset, update

Роутеры для масштабируемых проектов

Polling с автовыводом информации о боте

## Класс Bot: основные методы

| Метод                  | Описание                                              |
| ---------------------- | ----------------------------------------------------- |
| `get_me()`             | Получить информацию о боте                            |
| `send_message(...)`    | Отправить текстовое сообщение с поддержкой клавиатуры |
| `send_file(...)`       | Отправить файл (фото, аудио, видео, документ)         |
| `update_message(...)`  | Изменить (отредактировать) уже отправленное сообщение |
| `delete_message(...)`  | Удалить сообщение                                     |
| `answer_callback(...)` | Ответить на callback-запрос от inline-кнопки          |
| `download_media(...)`  | Скачать медиафайл по прямой ссылке                    |
Все методы асинхронные!

## Пример работы с медиа

```python
@dp.message()
async def on_message(msg: Message):
    # Скачать первое аудио-вложение из сообщения
    audio = msg.get_attachment("audio")
    if audio:
        await audio.download(bot, "voice.ogg")

    # Скачать все фото
    for img in msg.get_attachments("image"):
        await img.download(bot)
```
        

## FSM (Finite State Machine)
```python
from maxbot.fsm import State, StatesGroup

class Form(StatesGroup):
    name = State()
    age = State()

@dp.message()
async def on_message(msg: Message):
    await msg.set_state(Form.name)
    # ...
    state = await msg.get_state()
    data = await msg.get_data()
    await msg.update_data(name="Вова")
    await msg.reset_state()
```
set_state(state)

get_state()

reset_state()

update_data(key=value, ...)

get_data()

## Роутеры (Router)
```python
from maxbot.router import Router

router = Router()

@router.message()
async def any_text(message):
    await message.reply("Любой текст!")

@router.callback()
async def on_callback(cb):
    await cb.answer("Кнопка нажата!")

@router.bot_started
async def on_bot_started(update):
    print("Пользователь запустил бота!")

# Подключить роутер к диспетчеру
dp.include_router(router)
```

## Фильтры и StateFilter
```python
from maxbot.filters import F, StateFilter, TextStartsFilter

@dp.message(F.text == "привет")
async def on_hello(msg):
    await msg.reply("И тебе привет!")

@dp.message(StateFilter(Form.name))
async def on_state_name(msg):
    await msg.reply("Введите имя...")

@dp.callback(TextStartsFilter("edit_"))
async def on_edit(cb):
    await cb.answer("Редактирование!")
```

## Inline-клавиатуры
```python
kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Открыть сайт", url="https://max.ru")],
    [InlineKeyboardButton(text="Ответить", callback_data="answer")]
])
await bot.send_message(chat_id=123, text="Выберите:", reply_markup=kb)
```


## Типы и структуры данных
Message — объект сообщения (id, text, sender, chat, attachments, FSM-методы)

Attachment — объект вложения (type, url, token, id, download(...))

Callback — callback от инлайн-кнопки (payload, user, message, FSM-методы)

InlineKeyboardMarkup / InlineKeyboardButton — инлайн-клавиатуры

Dispatcher / Router — архитектура хендлеров

State, StatesGroup — описание и группировка состояний

FilterExpression / StateFilter / TextStartsFilter — фильтрация событий
## Пример структуры update с вложением
```json
{
  "message": {
    "body": {
      "attachments": [
        {
          "type": "audio",
          "payload": {
            "url": "https://.../file.ogg",
            "token": "...",
            "id": "1000123456789"
          }
        }
      ]
    }
  }
}
```
## Для скачивания используй:
msg.get_attachment("audio").download(bot, "voice.ogg")

## MAXBot — быстрый старт, максимальная скорость, знакомый синтаксис для ваших ботов в MAX.
=======

