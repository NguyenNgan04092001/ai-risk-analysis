import csv
import json
import hashlib
import time

from pathlib import Path

from src.attack_runner import AttackRunner
from src.data_loader import load_test_cases


ROOT = Path(__file__).resolve().parents[1]


class ExperimentManager:

    def __init__(
        self,
        experiment_id: str = "experiment_001",
        delay: float = 4.0
    ):

        self.experiment_id = experiment_id
        self.delay = delay

        self.output_dir = (
            ROOT / "results" / "experiments" / experiment_id
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.test_cases = load_test_cases()

        self.runners = {
            mode: AttackRunner(mode=mode, delay=delay)
            for mode in ("baseline", "protected")
        }

        self.results_file = (
            self.output_dir / "results.jsonl"
        )

        self.metadata_file = (
            self.output_dir / "experiment.json"
        )

        self.check_configuration()

    def check_configuration(self):
        """Проверка неизменности условий эксперимента."""

        files = [
            "data/test_cases.json",
            "data/customers.json",
            "data/bank_info.json",
            "data/fmea_config.json",
            "data/risk_catalog.json",
            "prompts/baseline.txt",
            "prompts/guardrails.txt",
            "src/llm_client.py",
            "src/bank_assistant.py",
            "src/evaluator.py",
            "src/attack_runner.py",
            "src/fmea.py",
            "src/risk_analyzer.py",
            "src/experiment.py"
        ]

        hashes = {}

        for filename in files:

            content = (ROOT / filename).read_bytes()

            hashes[filename] = hashlib.sha256(
                content
            ).hexdigest()

        llm = self.runners["baseline"].assistant.llm

        config = {
            "experiment_id": self.experiment_id,
            "provider": llm.provider,
            "base_url": llm.base_url,
            "model": llm.model,
            "total_scenarios": len(self.test_cases),
            "file_hashes": hashes
        }

        if self.metadata_file.exists():

            saved_config = json.loads(
                self.metadata_file.read_text(
                    encoding="utf-8"
                )
            )

            if saved_config != config:

                raise RuntimeError(
                    "Конфигурация эксперимента изменилась. "
                    "Создайте новый эксперимент."
                )

        else:

            self.metadata_file.write_text(
                json.dumps(
                    config,
                    ensure_ascii=False,
                    indent=4
                ),
                encoding="utf-8"
            )

    def load_results(self) -> list:
        """Загрузка сохранённых результатов."""

        if not self.results_file.exists():
            return []

        results = []

        with self.results_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if line.strip():
                    results.append(json.loads(line))

        return results

    def save_result(self, result: dict):
        """Сохранение результата одного запроса."""

        with self.results_file.open(
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(
                    result,
                    ensure_ascii=False
                ) + "\n"
            )

            file.flush()

    def get_completed(self) -> set:
        """Получение завершённых тестовых сценариев."""

        return {
            (row["mode"], row["test_id"])
            for row in self.load_results()
            if row["status"] in ("PASS", "FAIL")
        }

    def get_progress(self) -> dict:
        """Расчёт прогресса эксперимента."""

        completed = self.get_completed()

        total = len(self.test_cases) * 2

        return {
            "total": total,
            "completed": len(completed),
            "remaining": total - len(completed),
            "progress_percent": round(
                len(completed) / total * 100,
                2
            )
        }

    def run(self, max_requests: int = 40):
        """Выполнение очередного этапа эксперимента."""

        completed = self.get_completed()

        request_count = 0

        print("Эксперимент:", self.experiment_id)
        print("Максимум запросов:", max_requests)
        print("Прогресс:", self.get_progress())
        print("-" * 60)

        for test_case in self.test_cases:

            for mode in ("baseline", "protected"):

                test_id = test_case["test_id"]

                key = (mode, test_id)

                # Пропуск завершённых тестов
                if key in completed:
                    continue

                # Проверка лимита текущего запуска
                if request_count >= max_requests:

                    print("Лимит текущего запуска достигнут.")

                    self.export_csv()

                    return self.get_progress()

                print(
                    f"{test_id} | "
                    f"{test_case['risk_id']} | "
                    f"{mode}"
                )

                result = self.runners[mode].run_case(
                    test_case
                )

                request_count += 1

                self.save_result(result)

                print("Статус:", result["status"])
                print("Ответ:", result["response"])
                print("Причина:", result["reason"])

                # Остановка при технической ошибке
                if result["status"] == "ERROR":

                    print(
                        "Эксперимент приостановлен "
                        "из-за технической ошибки."
                    )

                    self.export_csv()

                    return self.get_progress()

                completed.add(key)

                print(
                    "Прогресс:",
                    len(completed),
                    "/",
                    len(self.test_cases) * 2
                )

                print("-" * 60)

                time.sleep(self.delay)

        self.export_csv()

        print("Эксперимент завершён.")

        return self.get_progress()

    def export_csv(self):
        """Экспорт результатов по режимам работы."""

        latest = {}

        for row in self.load_results():

            key = (row["mode"], row["test_id"])

            latest[key] = row

        for mode in ("baseline", "protected"):

            selected = [
                row.copy()
                for row in latest.values()
                if row["mode"] == mode
            ]

            if not selected:
                continue

            selected.sort(
                key=lambda row: row["test_id"]
            )

            for row in selected:

                row["matched_markers"] = json.dumps(
                    row["matched_markers"],
                    ensure_ascii=False
                )

            output_path = (
                self.output_dir / f"{mode}.csv"
            )

            temp_path = output_path.with_suffix(".tmp")

            with temp_path.open(
                "w",
                encoding="utf-8-sig",
                newline=""
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=list(selected[0].keys())
                )

                writer.writeheader()
                writer.writerows(selected)

            temp_path.replace(output_path)

            print("Сохранено:", output_path)