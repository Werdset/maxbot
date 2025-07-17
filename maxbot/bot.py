import mimetypes
import asyncio
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
            chat_id: Optional[int] = None,
            user_id: Optional[int] = None,
            text: str = "",
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            notify: bool = True,
            format: Optional[str] = None
    ):
        if not (chat_id or user_id):
            raise ValueError("Нужно передать хотя бы один из параметров: chat_id или user_id")

        params = {
            "access_token": self.token
        }

        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id

        json_body = {
            "text": text,
            "notify": str(notify).lower(),  # если API принимает как "true"/"false"
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
        resp = await self._request("POST", "/uploads", params={"type": media_type})
        upload_url = resp.get("url")
        if not upload_url:
            raise ValueError("Не удалось получить URL для загрузки")

        # Загружаем файл
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            files = {"data": (file_path, f, mime_type or "application/octet-stream")}
            async with httpx.AsyncClient() as client:
                upload_resp = await client.post(upload_url, files=files)
                upload_resp.raise_for_status()

                print("[DEBUG] upload_resp.status_code:", upload_resp.status_code)
                print("[DEBUG] upload_resp.text:", upload_resp.text)

                # Для видео и аудио токен будет в ответе сразу
                if media_type in ("video", "audio"):
                    result = upload_resp.json()
                    if "token" in result:
                        return result["token"]

                # Для изображений и файлов токен возвращается в ответе на загрузку
                if media_type == "image":
                    try:
                        result = upload_resp.json()
                        print("[DEBUG] result:", result)
                    except ValueError:
                        raise ValueError("Не удалось распарсить JSON в ответе от сервера")

                    if "photos" in result and result["photos"]:
                        photo_key = next(iter(result["photos"]))
                        token = result["photos"][photo_key].get("token")
                        if token:
                            print(f"[DEBUG] Извлечённый токен: {token}")
                            return token
                    raise ValueError("Не найден токен для изображения")

                if media_type == "file":
                    try:
                        result = upload_resp.json()
                        if "token" in result:
                            return result["token"]
                    except ValueError:
                        raise ValueError("Не удалось распарсить JSON для файла")

        return None

    async def send_file(
            self,
            file_path: str,
            media_type: str,
            chat_id: Optional[int] = None,
            user_id: Optional[int] = None,
            text: str = "",
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            notify: bool = True,
            format: Optional[str] = None, max_retries=3
    ):
        # Загрузка файла на сервер
        tokens = await self.upload_file(file_path, media_type)
        if not tokens:
            raise ValueError("Не удалось получить токен для файла")

        print("token:", tokens)
        await asyncio.sleep(5)

        # Базовое вложение — медиафайл
        attachments = [
            {
                "type": media_type,
                "payload": {"token": tokens}
            }
        ]

        # Если передана клавиатура — добавляем её как вложение
        if reply_markup:
            attachments.append(reply_markup.to_attachment())

        # Параметры и тело запроса — как в send_message
        params = {
            "access_token": self.token,
        }
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id
        json_body = {
            "text": text,
            "notify": notify,
            "attachments": attachments,
        }

        if format:
            json_body["format"] = format

        print("[send_file] params:", params)
        print("[send_file] json:", json_body)

        delay = 2  # секунд ожидания между попытками
        for attempt in range(1, max_retries + 1):
            resp = await self.client.post(
                f"{self.base_url}/messages",
                params=params,
                json=json_body,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            print(f"Attempt {attempt}: RESP:", resp.status_code)
            print("RESP_TEXT:", resp.text)
            if resp.status_code != 400:
                return resp
            if "attachment.not.ready" in resp.text or "not.processed" in resp.text:
                print(f"Жду {delay} секунд и пробую еще раз...")
                await asyncio.sleep(delay)
            else:
                # Какая-то другая ошибка, повторять не имеет смысла
                break
        return resp

    async def download_media(self, url: str, dest_path: str = None):
        """
        Скачивает медиафайл по прямой ссылке (url) и сохраняет на диск.
        Если dest_path не указан — берётся имя файла из url.
        """
        if dest_path is None:
            filename = url.split("?")[0].split("/")[-1] or "file.bin"
            ext = mimetypes.guess_extension((await self._get_content_type(url)) or "")
            if ext and not filename.endswith(ext):
                filename += ext
            dest_path = filename

        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, timeout=120) as response:
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        f.write(chunk)
        print(f"[Bot] Файл скачан: {dest_path}")
        return dest_path

    async def _get_content_type(self, url):
        async with httpx.AsyncClient() as client:
            resp = await client.head(url)
            return resp.headers.get("content-type")







