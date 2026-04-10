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

    async def _request(self, method: str, path: str, params=None, json=None, headers=None):
        if params is None:
            params = {}

        if headers is None:
            headers = {}

        headers.update({
            "Content-Type": "application/json",
            "Authorization": self.token  # ❗ теперь только тут
        })

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
            print(f"[Bot] Ответ сервера: {e.response.status_code} {e.response.text}")
            raise
        except httpx.ReadTimeout:
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
            raise ValueError("Нужно передать chat_id или user_id")

        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id

        json_body = {
            "text": text,
            "notify": notify  # ✅ bool, не строка
        }

        if format:
            json_body["format"] = format

        if reply_markup:
            json_body["attachments"] = [reply_markup.to_attachment()]

        return await self._request(
            "POST",
            "/messages",
            params=params,
            json=json_body
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

    async def update_message(
        self,
        message_id: str,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        notify: bool = True,
        format: Optional[str] = None):

        params = {
        "access_token": self.token,
        "message_id": message_id,
        }

        json_body = {
        "text": text,
        "notify": notify,
        }

        if format:
            json_body["format"] = format

    # 👉 Если есть клавиатура — ставим её
        if reply_markup:
            json_body["attachments"] = [reply_markup.to_attachment()]
        else:
        # 👉 Если нет — явно очищаем
            json_body["attachments"] = []


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

    async def upload_file(self, file_path: str, media_type: str) -> dict:
    # 1. Запрашиваем upload URL и токен
        resp = await self._request("POST", "/uploads", params={"type": media_type})
        print(resp)
        upload_url = resp["url"]
        file_token = resp.get("token")

        mime_type, _ = mimetypes.guess_type(file_path)

    # 2. Загружаем файл
        with open(file_path, "rb") as f:
            files = {"data": (file_path, f, mime_type or "application/octet-stream")}

            async with httpx.AsyncClient() as client:
                upload_resp = await client.post(
                    upload_url,
                    files=files,
                    headers={"Authorization": self.token},
                )
                upload_resp.raise_for_status()
                print(upload_resp)
            # Для image/file: получаем token из JSON ответа
                if media_type == "file":
                    try:
                        upload_json = upload_resp.json()
                        file_token = upload_json.get("token")
                    except ValueError:
                        raise ValueError("MAX API вернул некорректный JSON для image/file")
                    
                if media_type == "image":
                    result = upload_resp.json()
                    if "photos" in result and result["photos"]:
                        first_size = next(iter(result["photos"].values()))
                        token = first_size.get("token")
                        if token:
                            return {"token": token}
                    raise ValueError("Не найден токен для изображения")
            # Для audio/video: token уже есть в resp, JSON ждать не нужно
        print(file_token)
        return {"token": file_token}

    async def message_reply(
        self,
        message_id: str,  # mid — на что отвечаем
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        text: str = "",
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        notify: bool = True,
        format: Optional[str] = None
        ):
        if not (chat_id or user_id):
            raise ValueError("Нужно передать chat_id или user_id")

        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id

        json_body = {
            "text": text,
            "notify": notify,
            "link": {
                "type": "reply",   # ❗ ключевой момент
                "mid": message_id  # ❗ id сообщения
            }
        }

        if format:
            json_body["format"] = format

        if reply_markup:
            json_body["attachments"] = [reply_markup.to_attachment()]

        return await self.client.post(
            f"{self.base_url}/messages",
            params=params,
            json=json_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": self.token  # ❗ обязательно
            },
            timeout=httpx.Timeout(30.0)
        )

    async def send_file(
        self,
        file_path: str,
        media_type: str,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        text: str = "",
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        notify: bool = True,
        format: Optional[str] = None,
        max_retries: int = 10
    ):
    # 1. Получаем payload (а не token!)
        payload = await self.upload_file(file_path, media_type)
        print(payload)
    # 2. Формируем attachments
        attachments = [
            {
                "type": media_type,
                "payload": payload  # ❗ ключевое изменение
            }
            ]

        #if reply_markup:
            #attachments.append(reply_markup.to_attachment())

        json_body = {
            "text": text,
            #"notify": str(notify).lower(),
            "attachments": attachments
            }

        if format:
            json_body["format"] = format

        if not (chat_id or user_id):
            raise ValueError("Нужно передать chat_id или user_id")

        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.token  # ❗ теперь тут
            }

    # 3. Ретраи с backoff (улучшил сразу)
        delay = 2

        for attempt in range(1, max_retries + 1):
            resp = await self.client.post(
                f"{self.base_url}/messages",
                params=params,
                json=json_body,
                headers=headers,
                timeout=60
            )
            print(json_body)
            print(resp)
            if resp.status_code < 400:
                return resp


            if (
                "attachment.not.ready" in resp.text
                or "not.processed" in resp.text
                ):
                print(f"Попытка {attempt}: файл обрабатывается, ждём {delay} сек...")
                await asyncio.sleep(delay)
                delay *= 2
                continue

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












