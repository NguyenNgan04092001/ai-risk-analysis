import csv
import json
import time
from pathlib import Path
from datetime import datetime, timezone

from src.bank_assistant import BankAssistant
from src.data_loader import load_test_cases
from src.evaluator import ResponseEvaluator


ROOT = Path(__file__).resolve().parents[1]


class AttackRunner:
    def __init__(
        self,
        mode: str = "baseline",
        delay: float = 4.0
    ):

        self.mode = mode

        self.assistant = BankAssistant(mode=mode)
        self.evaluator = ResponseEvaluator()
        self.test_cases = load_test_cases()
        self.delay = delay

    def run_case(self, test_case: dict) -> dict:
        """Выполнение одного тестового сценария."""

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "test_id": test_case["test_id"],
            "risk_id": test_case["risk_id"],
            "description": test_case["description"],
            "customer_id": test_case["customer_id"],
            "prompt": test_case["prompt"],
            "expected_behavior": test_case["expected_behavior"],
            "response": "",
            "status": "ERROR",
            "attack_success": None,
            "matched_markers": [],
            "reason": "",
            "model": "",
            "finish_reason": "",
            "prompt_tokens": None,
            "completion_tokens": None,
            "duration": 0.0
        }

        start_time = time.perf_counter()

        try:
            # Отправка запроса банковскому ассистенту
            response = self.assistant.ask(
                question=test_case["prompt"],
                customer_id=test_case["customer_id"]
            )

            result["response"] = response

            # Автоматическая оценка ответа
            evaluation = self.evaluator.evaluate(
                test_case,
                response
            )

            result.update(evaluation)

        except Exception as e:
            result["status"] = "ERROR"
            result["reason"] = str(e)

        finally:
            # Сохранение метаданных ответа
            metadata = self.assistant.llm.last_metadata

            result.update(metadata)

            result["duration"] = round(
                time.perf_counter() - start_time,
                3
            )

        return result

    def run_all(self) -> list:
        """Выполнение всех тестовых сценариев."""

        results = []

        output_path = (
            ROOT / "results" / f"{self.mode}.csv"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        total = len(self.test_cases)

        print("Начало тестирования")
        print("Режим работы:", self.mode)
        print("Модель:", self.assistant.llm.model)
        print("Количество сценариев:", total)
        print("-" * 50)

        with output_path.open(
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            writer = None

            for index, test_case in enumerate(
                self.test_cases,
                start=1
            ):

                print(
                    f"[{index}/{total}] "
                    f"{test_case['test_id']} | "
                    f"{test_case['risk_id']}"
                )

                result = self.run_case(test_case)

                results.append(result)

                # Подготовка данных для CSV
                csv_row = result.copy()

                csv_row["matched_markers"] = json.dumps(
                    result["matched_markers"],
                    ensure_ascii=False
                )

                if writer is None:

                    writer = csv.DictWriter(
                        file,
                        fieldnames=list(csv_row.keys())
                    )

                    writer.writeheader()

                writer.writerow(csv_row)

                # Немедленное сохранение результата
                file.flush()

                print("Статус:", result["status"])
                print("Ответ:", result["response"])
                print("Причина:", result["reason"])
                print("Время:", result["duration"], "сек.")
                print("-" * 50)

                # Ограничение частоты запросов
                if index < total:
                    time.sleep(self.delay)

        print("Тестирование завершено")
        print("Результаты сохранены:", output_path)

        return results