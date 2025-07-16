import requests
import config
from typing import List

async def query_gemini_api(messages: List[dict], model="google/gemini-2.0-flash-001", temperature: float = 0.6) -> str:
    """
    Отправляет запрос к API и возвращает ответ.
    Принимает на вход готовый список сообщений.
    """
    url = config.API_ENDPOINT
    headers = {
        "Authorization": f"Bearer {config.AI_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Вызовет исключение для статусов 4xx/5xx
        response_data = response.json()

        if response_data.get("choices"):
            return response_data["choices"][0]["message"]["content"].strip()

        # Если в ответе нет 'choices', возвращаем ошибку
        return "Ошибка: API вернул пустой ответ."

    except requests.exceptions.RequestException as e:
        print(f"🚫 Ошибка сети или API: {e}")
        return "Произошла ошибка при подключении к API. Попробуйте позже."
    except Exception as e:
        print(f"🚫 Неизвестная ошибка в ai_api: {e}")
        return "Произошла внутренняя ошибка. Обратитесь в поддержку."