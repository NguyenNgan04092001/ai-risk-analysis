import json
from pathlib import Path

from src.data_loader import load_bank_info, load_customers
from src.llm_client import LLMClient


ROOT = Path(__file__).resolve().parents[1]


class BankAssistant:

    def __init__(self, mode: str = "baseline"):

        # Проверка режима работы
        if mode not in ("baseline", "protected"):
            raise ValueError(
                f"Неизвестный режим: {mode}"
            )

        self.mode = mode

        self.llm = LLMClient()
        self.bank_info = load_bank_info()
        self.customers = load_customers()

        self.base_prompt = (
            ROOT / "prompts" / "baseline.txt"
        ).read_text(encoding="utf-8")

        self.guardrails = ""

        # Загрузка дополнительных правил защиты
        if self.mode == "protected":

            self.guardrails = (
                ROOT / "prompts" / "guardrails.txt"
            ).read_text(encoding="utf-8")

    def build_system_prompt(
        self,
        customer_id: str
    ) -> str:

        context = {
            "authenticated_customer_id": customer_id,
            "bank_info": self.bank_info,
            "customers": self.customers
        }

        context_text = json.dumps(
            context,
            ensure_ascii=False,
            indent=2
        )

        system_prompt = self.base_prompt

        # Применение дополнительных правил защиты
        if self.mode == "protected":

            system_prompt += (
                "\n\n" + self.guardrails
            )

        system_prompt += (
            "\n\nБанковский контекст:\n"
            + context_text
        )

        return system_prompt

    def ask(
        self,
        question: str,
        customer_id: str
    ) -> str:

        system_prompt = self.build_system_prompt(
            customer_id
        )

        return self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=question
        )