from pydantic import BaseModel, Field
from typing import List, Optional

class User(BaseModel):
    id: int = Field(alias="user_id")
    first_name: str = ""
    last_name: str = ""
    name: str = ""

    class Config:
        populate_by_name = True

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

class Callback(BaseModel):
    callback_id: str
    payload: str
    user: User

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