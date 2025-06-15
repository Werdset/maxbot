from pydantic import BaseModel, Field
from typing import List, Optional

from maxbot.fsm import State


class User(BaseModel):
    id: int = Field(alias="user_id")
    first_name: str = ""
    last_name: str = ""
    is_bot: Optional[bool] = None
    name: str = ""
    last_activity_time: Optional[int] = 0

    class Config:
        populate_by_name = True


class Recipient(BaseModel):
    chat_id: int
    chat_type: str
    user_id: int

class Chat(BaseModel):
    id: int
    type: str

class Message(BaseModel):
    id: str
    text: str
    chat: Chat
    sender: User

    @classmethod
    def from_raw(cls, raw: dict):
        return cls(
            id=raw["body"]["mid"],
            text=raw["body"]["text"],
            chat=Chat(id=raw["recipient"]["chat_id"], type=raw["recipient"]["chat_type"]),
            sender=User(user_id=raw["sender"]["user_id"], name=raw["sender"]["name"])
        )

    @property
    def dispatcher(self):
        from maxbot.dispatcher import get_current_dispatcher  # 👈 импорт внутри метода
        return get_current_dispatcher()

    def user_id(self) -> int:
        return self.sender.id

    async def set_state(self, state: State):
        self.dispatcher.storage.set_state(self.user_id(), state)

    async def get_state(self) -> Optional[str]:
        return self.dispatcher.storage.get_state(self.user_id())

    async def reset_state(self):
        self.dispatcher.storage.reset_state(self.user_id())

    async def update_data(self, **kwargs):
        self.dispatcher.storage.update_data(self.user_id(), **kwargs)

    async def get_data(self) -> dict:
        return self.dispatcher.storage.get_data(self.user_id())


class Callback(BaseModel):
    callback_id: str
    payload: str
    user: User
    message: Message

    @property
    def dispatcher(self):
        from maxbot.dispatcher import get_current_dispatcher  # 👈 импорт внутри метода
        return get_current_dispatcher()

    def user_id(self) -> int:
        return self.user.id

    async def set_state(self, state: State):
        self.dispatcher.storage.set_state(self.user_id(), state)

    async def get_state(self) -> Optional[str]:
        return self.dispatcher.storage.get_state(self.user_id())

    async def reset_state(self):
        self.dispatcher.storage.reset_state(self.user_id())

    async def update_data(self, **kwargs):
        self.dispatcher.storage.update_data(self.user_id(), **kwargs)

    async def get_data(self) -> dict:
        return self.dispatcher.storage.get_data(self.user_id())


class InlineKeyboardButton(BaseModel):
    text: str
    callback_data: str

    def to_dict(self):
        return {
            "type": "callback",
            "text": self.text,
            "payload": self.callback_data
        }

class InlineKeyboardMarkup(BaseModel):
    inline_keyboard: List[List[InlineKeyboardButton]]

    def to_attachment(self):
        return {
            "type": "inline_keyboard",
            "payload": {
                "buttons": [
                    [button.to_dict() for button in row]
                    for row in self.inline_keyboard
                ]
            }
        }