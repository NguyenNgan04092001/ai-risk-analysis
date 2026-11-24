import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env", override=True)


class LLMClient:

    def __init__(self):

        # Выбор поставщика LLM
        self.provider = os.getenv(
            "LLM_PROVIDER", "openrouter"
        ).strip().lower()

        providers = {
            "openrouter": {
                "prefix": "OPENROUTER",
                "base_url": "https://openrouter.ai/api/v1"
            },
            "groq": {
                "prefix": "GROQ",
                "base_url": "https://api.groq.com/openai/v1"
            },
            "ollama": {
                "prefix": "OLLAMA",
                "base_url": "http://localhost:11434/v1"
            }
        }

        if self.provider not in providers:
            raise ValueError(
                f"Неизвестный поставщик: {self.provider}"
            )

        config = providers[self.provider]
        prefix = config["prefix"]

        api_key = os.getenv(
            f"{prefix}_API_KEY", ""
        ).strip()

        # Локальная модель не требует API-ключа
        if self.provider == "ollama":
            api_key = api_key or "ollama"

        if not api_key:
            raise ValueError(
                f"API-ключ не найден: {prefix}"
            )

        self.model = os.getenv(
            f"{prefix}_MODEL", ""
        ).strip()

        if not self.model:
            raise ValueError(
                "Модель не указана"
            )

        self.base_url = os.getenv(
            f"{prefix}_BASE_URL",
            config["base_url"]
        )

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=60.0,
            max_retries=0
        )

        # Метаданные последнего ответа
        self.last_metadata = {}

    def generate(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:

        # Очистка предыдущих метаданных
        self.last_metadata = {}

        params = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0
        }

        # Настройки конкретного поставщика
        if self.provider == "groq":

            params["max_completion_tokens"] = 512

            if self.model == "qwen/qwen3.8-27b":

                params["extra_body"] = {
                    "reasoning_effort": "none"
                }

        else:

            params["max_tokens"] = 2048

        # Запрос к языковой модели
        response = self.client.chat.completions.create(
            **params
        )

        choice = response.choices[0]

        content = (
            choice.message.content or ""
        ).strip()

        # Сохранение метаданных
        self.last_metadata = {
            "model": response.model,
            "finish_reason": choice.finish_reason,
            "prompt_tokens": (
                response.usage.prompt_tokens
                if response.usage else None
            ),
            "completion_tokens": (
                response.usage.completion_tokens
                if response.usage else None
            )
        }

        # Проверка соответствия модели
        if response.model != self.model:

            raise RuntimeError(
                f"Несоответствие модели: "
                f"ожидалась {self.model}, "
                f"получена {response.model}"
            )

        # Проверка полноты ответа
        if choice.finish_reason == "length":

            raise RuntimeError(
                "Превышен лимит токенов"
            )

        # Проверка наличия ответа
        if not content:

            raise RuntimeError(
                "Получен пустой ответ от модели"
            )

        return content