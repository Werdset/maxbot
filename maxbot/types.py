from pydantic import BaseModel, Field
from typing import List, Optional, Literal

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


class Attachment(BaseModel):
    type: str
    url: Optional[str] = None
    token: Optional[str] = None
    id: Optional[str] = None

    async def download(self, bot, dest_path: Optional[str] = None):
        if not self.url:
            raise ValueError("У вложения нет url для скачивания")
        return await bot.download_media(self.url, dest_path)

class Message(BaseModel):
    id: str
    text: str
    chat: Chat
    sender: User
    forward_from: Optional[User] = None
    forward_mid: Optional[str] = None
    attachments: List[Attachment] = []

    @classmethod
    def from_raw(cls, raw: dict):
        link = raw.get("link", {})
        forward_user = link.get("sender")
        forward_msg = link.get("message")
        body = raw.get("body", {})

        # Парсим вложения:
        attachments = []
        for att in body.get("attachments", []):
            payload = att.get("payload", {})
            attachments.append(Attachment(
                type=att.get("type"),
                url=payload.get("url"),
                token=payload.get("token"),
                id=payload.get("id"),
            ))

        return cls(
            id=body["mid"],
            text=body.get("text", ""),
            chat=Chat(id=raw["recipient"]["chat_id"], type=raw["recipient"]["chat_type"]),
            sender=User(user_id=raw["sender"]["user_id"], name=raw["sender"]["name"]),
            forward_from=User(**forward_user) if forward_user else None,
            forward_mid=forward_msg["mid"] if forward_msg else None,
            attachments=attachments
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

    def get_attachment(self, type_: str) -> Optional[Attachment]:
        """
        Вернёт первое вложение указанного типа (например, 'audio', 'image'), либо None.
        """
        return next((a for a in self.attachments if a.type == type_), None)

    def get_attachments(self, type_: str) -> List[Attachment]:
        """
        Вернёт список всех вложений указанного типа.
        """
        return [a for a in self.attachments if a.type == type_]




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
    callback_data: Optional[str] = None
    url: Optional[str] = None
    type: Optional[Literal["callback", "link", "request_geo_location", "request_contact", "chat"]] = None

    def to_dict(self):
        btn_type = self.type

        if not btn_type:
            # Автоопределение по наличию полей
            if self.url:
                btn_type = "link"
            else:
                btn_type = "callback"

        data = {
            "type": btn_type,
            "text": self.text,
        }

        if btn_type == "link" and self.url:
            data["url"] = self.url
        elif self.callback_data:
            data["payload"] = self.callback_data

        return data

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