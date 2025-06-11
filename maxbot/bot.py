import mimetypes

import httpx
from typing import Optional
from .types import InlineKeyboardMarkup

class Bot:
    BASE_URL = "https://botapi.max.ru"

    def __init__(self, token: str):
        self.token = token
        self.base_url = self.BASE_URL
        self.client = httpx.AsyncClient()

    async def _request(self, method: str, path: str, params=None, json=None):
        if params is None:
            params = {}
        params["access_token"] = self.token  # 👈 всегда добавляем токен
        headers = {"Content-Type": "application/json"}
        try:
            response = await self.client.request(
                method=method,
                url=self.base_url + path,
                params=params,
                json=json,
                headers=headers,
                timeout=httpx.Timeout(30.0)
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"[Bot] Ошибка запроса: {e}")
            print(f"[Bot] Ответ сервера: {e.response.status_code} {e.response.text}")  # 👈 вот это ключ
            raise
        except httpx.ReadTimeout:
            print("[Bot] Таймаут при ожидании ответа (нормально для long polling)")
            return {}

    async def get_me(self):
        return await self._request("GET", "/me")

    async def send_message(
            self,
            chat_id: int,
            text: str,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            notify: bool = True,
            format: Optional[str] = None
    ):
        params = {
            "access_token": self.token,
            "user_id": chat_id,
             # API может ожидать "true"/"false"
        }

        json_body = {
            "text": text,
            "notify": notify,
        }

        if format:
            json_body["format"] = format

        if reply_markup:
            json_body["attachments"] = [reply_markup.to_attachment()]

        print("[send_message] params:", params)
        print("[send_message] json:", json_body)

        return await self.client.post(
            f"{self.base_url}/messages",
            params=params,
            json=json_body,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(30.0)
        )

    async def answer_callback(self, callback_id: str, notification: str):
        print("[Bot] ➤ Ответ на callback:", {
            "callback_id": callback_id,
            "notification": notification
        })
        return await self._request(
            "POST",
            "/answers",
            params={"callback_id": callback_id},
            json={"notification": notification}
        )

    async def update_message(self,
            message_id: str,
            text: str,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            notify: bool = True,
            format: Optional[str] = None):

        params = {
            "access_token": self.token,
            "message_id": message_id,
            # API может ожидать "true"/"false"
        }

        json_body = {
            "text": text,
            "notify": notify,
        }

        if format:
            json_body["format"] = format

        if reply_markup:
            json_body["attachments"] = [reply_markup.to_attachment()]

        print("[send_message] params:", params)
        print("[send_message] json:", json_body)

        return await self.client.put(
            f"{self.base_url}/messages",
            params=params,
            json=json_body,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(30.0)
        )


    async def delete_message(self, message_id: str):
        params = {
            "access_token": self.token,
            "message_id": message_id,
            # API может ожидать "true"/"false"
        }

        return await self.client.delete(
            f"{self.base_url}/messages",
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(30.0)
        )


    async def upload_file(self, file_path: str, media_type: str) -> str:
        # 1. Получаем URL загрузки
        resp = await self._request(
            "POST",
            "/uploads",
            params={"type": media_type}
        )
        upload_url = resp["url"]

        # 2. Загружаем файл по upload_url
        mime_type, _ = mimetypes.guess_type(file_path)
        files = {"data": (file_path, open(file_path, "rb"), mime_type or "application/octet-stream")}

        async with httpx.AsyncClient() as client:
            upload_resp = await client.post(upload_url, files=files)
            upload_resp.raise_for_status()
            result = upload_resp.json()
            return result["token"]

    async def send_file(
            self,
            chat_id: int,
            file_path: str,
            media_type: str,
            text: str = "",
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            notify: bool = True,
            format: Optional[str] = None
    ):
        # Загрузка файла на сервер
        token = await self.upload_file(file_path, media_type)

        # Базовое вложение — медиафайл
        attachments = [
            {
                "type": media_type,
                "payload": {"token": token}
            }
        ]

        # Если передана клавиатура — добавляем её как вложение
        if reply_markup:
            attachments.append(reply_markup.to_attachment())

        # Параметры и тело запроса — как в send_message
        params = {
            "access_token": self.token,
            "user_id": chat_id,
        }

        json_body = {
            "text": text,
            "notify": notify,
            "attachments": attachments,
        }

        if format:
            json_body["format"] = format

        print("[send_file] params:", params)
        print("[send_file] json:", json_body)

        return await self.client.post(
            f"{self.base_url}/messages",
            params=params,
            json=json_body,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(30.0)
        )







