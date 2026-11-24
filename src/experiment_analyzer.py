import csv
import json
import hashlib
import re

from pathlib import Path

from src.data_loader import load_test_cases
from src.risk_analyzer import RiskAnalyzer


ROOT = Path(__file__).resolve().parents[1]

EXPERIMENTS_DIR = ROOT / "results" / "experiments"


class ExperimentAnalyzer:

    MODES = ("baseline", "protected")

    VALID_STATUSES = ("PASS", "FAIL")

    PILOT_IDS = {
        f"T{i:03d}" for i in range(1, 13)
    }

    def __init__(
        self,
        experiment_id: str = "experiment_002"
    ):

        if not re.fullmatch(
            r"[a-zA-Z0-9_-]+", experiment_id
        ):
            raise ValueError(
                "Некорректный идентификатор эксперимента"
            )

        self.experiment_id = experiment_id

        self.output_dir = (
            EXPERIMENTS_DIR / experiment_id
        )

        if not self.output_dir.exists():
            raise FileNotFoundError(
                f"Эксперимент не найден: {experiment_id}"
            )

        self.results_file = (
            self.output_dir / "results.jsonl"
        )

        self.metadata_file = (
            self.output_dir / "experiment.json"
        )

        self.test_cases = load_test_cases()

        self.cases_by_id = {
            case["test_id"]: case
            for case in self.test_cases
        }

        if len(self.cases_by_id) != len(self.test_cases):
            raise ValueError(
                "Обнаружены повторяющиеся ID сценариев"
            )

        self.analyzer = RiskAnalyzer()

        self.metadata = json.loads(
            self.metadata_file.read_text(
                encoding="utf-8"
            )
        )

        self.check_configuration()

    def check_configuration(self):
        """Проверка условий эксперимента."""

        if (
            self.metadata["total_scenarios"]
            != len(self.test_cases)
        ):
            raise RuntimeError(
                "Количество сценариев изменилось"
            )

        for filename, expected_hash in (
            self.metadata["file_hashes"].items()
        ):

            actual_hash = hashlib.sha256(
                (ROOT / filename).read_bytes()
            ).hexdigest()

            if actual_hash != expected_hash:
                raise RuntimeError(
                    f"Изменён файл: {filename}"
                )

    def load_attempts(self) -> list:
        """Загрузка всех попыток выполнения."""

        if not self.results_file.exists():
            return []

        rows = []

        with self.results_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if line.strip():
                    rows.append(json.loads(line))

        return rows

    def validate_result(self, row: dict):
        """Проверка соответствия результата сценарию."""

        test_id = row["test_id"]

        if test_id not in self.cases_by_id:
            raise ValueError(
                f"Неизвестный сценарий: {test_id}"
            )

        if row["mode"] not in self.MODES:
            raise ValueError(
                f"Неизвестный режим: {row['mode']}"
            )

        case = self.cases_by_id[test_id]

        for field in (
            "risk_id",
            "customer_id",
            "prompt"
        ):

            if row[field] != case[field]:
                raise ValueError(
                    f"{test_id}: несоответствие {field}"
                )

        status = row["status"]

        if status not in ("PASS", "FAIL", "ERROR"):
            raise ValueError(
                f"{test_id}: неизвестный статус"
            )

        if status in self.VALID_STATUSES:

            if row["model"] != self.metadata["model"]:
                raise ValueError(
                    f"{test_id}: модель не соответствует "
                    "конфигурации эксперимента"
                )

            if case["risk_id"] == "NORMAL":

                if row["attack_success"] is not None:
                    raise ValueError(
                        f"{test_id}: некорректный attack_success"
                    )

            else:

                expected = status == "FAIL"

                if row["attack_success"] is not expected:
                    raise ValueError(
                        f"{test_id}: противоречивый результат"
                    )

    def get_latest_results(self, attempts: list) -> dict:
        """Получение актуального результата каждого теста."""

        latest = {}

        for row in attempts:

            self.validate_result(row)

            key = (
                row["mode"],
                row["test_id"]
            )

            previous = latest.get(key)

            # Завершённый результат не заменяется ошибкой
            if (
                previous is not None
                and previous["status"] in self.VALID_STATUSES
            ):

                if row["status"] in self.VALID_STATUSES:
                    raise ValueError(
                        f"Повторный завершённый результат: {key}"
                    )

                continue

            latest[key] = row

        return latest

    def get_subset_ids(
        self,
        subset: str = "all"
    ) -> set:
        """Выбор экспериментального поднабора."""

        ids = set(self.cases_by_id)

        if subset == "all":
            return ids

        if subset == "new":
            return ids - self.PILOT_IDS

        if subset == "pilot":
            return ids & self.PILOT_IDS

        raise ValueError(
            f"Неизвестный поднабор: {subset}"
        )

    def get_paired_ids(
        self,
        latest: dict,
        selected_ids: set
    ) -> set:
        """Поиск завершённых пар Baseline–Protected."""

        return {
            test_id
            for test_id in selected_ids
            if all(
                latest.get(
                    (mode, test_id), {}
                ).get("status") in self.VALID_STATUSES

                for mode in self.MODES
            )
        }

    @staticmethod
    def ratio(
        numerator: int,
        denominator: int
    ):

        if denominator == 0:
            return None

        return round(
            numerator / denominator,
            6
        )

    def get_mode_statistics(
        self,
        latest: dict,
        attempts: list,
        selected_ids: set,
        mode: str
    ) -> dict:
        """Расчёт статистики выполнения эксперимента."""

        rows = [
            row
            for (row_mode, test_id), row
            in latest.items()
            if row_mode == mode
            and test_id in selected_ids
        ]

        valid = [
            row for row in rows
            if row["status"] in self.VALID_STATUSES
        ]

        errors = [
            row for row in rows
            if row["status"] == "ERROR"
        ]

        mode_attempts = [
            row for row in attempts
            if row["mode"] == mode
            and row["test_id"] in selected_ids
        ]

        error_attempts = sum(
            row["status"] == "ERROR"
            for row in mode_attempts
        )

        return {
            "expected": len(selected_ids),
            "completed": len(valid),
            "pending_errors": len(errors),
            "not_started": len(selected_ids) - len(rows),
            "remaining": len(selected_ids) - len(valid),
            "attempts": len(mode_attempts),
            "error_attempts": error_attempts,
            "coverage": self.ratio(
                len(valid),
                len(selected_ids)
            ),
            "error_rate": self.ratio(
                error_attempts,
                len(mode_attempts)
            )
        }

    def analyze_risks(
        self,
        latest: dict,
        selected_ids: set,
        paired_ids: set
    ) -> list:
        """Парный анализ категорий риска."""

        report = []

        for risk in self.analyzer.risks:

            risk_id = risk["risk_id"]

            expected_ids = {
                test_id
                for test_id in selected_ids
                if (
                    self.cases_by_id[test_id]["risk_id"]
                    == risk_id
                )
            }

            common_ids = expected_ids & paired_ids

            rows = {}

            for mode in self.MODES:

                rows[mode] = []

                for test_id in sorted(common_ids):

                    row = latest[
                        (mode, test_id)
                    ].copy()

                    # Совместимость с RiskAnalyzer
                    row["attack_success"] = str(
                        row["attack_success"]
                    )

                    rows[mode].append(row)

            result = self.analyzer.analyze_risk(
                risk,
                rows["baseline"],
                rows["protected"]
            )

            result["expected_scenarios"] = len(
                expected_ids
            )

            result["paired_scenarios"] = len(
                common_ids
            )

            result["pair_coverage"] = self.ratio(
                len(common_ids),
                len(expected_ids)
            )

            if not common_ids:

                result["evaluation_status"] = (
                    "Неполные данные"
                )

            elif common_ids == expected_ids:

                result["evaluation_status"] = (
                    "Завершена"
                )

            else:

                result["evaluation_status"] = (
                    "Предварительная"
                )

            report.append(result)

        return report

    def analyze_outcomes(
        self,
        latest: dict,
        selected_ids: set,
        paired_ids: set,
        normal: bool = False
    ) -> dict:
        """Расчёт ASR или точности обычных запросов."""

        expected_ids = {
            test_id
            for test_id in selected_ids
            if (
                self.cases_by_id[test_id]["risk_id"]
                == "NORMAL"
            ) == normal
        }

        common_ids = expected_ids & paired_ids

        result = {
            "metric": (
                "normal_accuracy" if normal
                else "asr"
            ),
            "expected_scenarios": len(expected_ids),
            "paired_scenarios": len(common_ids),
            "pair_coverage": self.ratio(
                len(common_ids),
                len(expected_ids)
            )
        }

        for mode in self.MODES:

            rows = [
                latest[(mode, test_id)]
                for test_id in common_ids
            ]

            if normal:

                positive = sum(
                    row["status"] == "PASS"
                    for row in rows
                )

            else:

                positive = sum(
                    row["attack_success"] is True
                    for row in rows
                )

            result[mode] = {
                "count": positive,
                "valid": len(rows),
                "value": self.ratio(
                    positive,
                    len(rows)
                )
            }

        before = result["baseline"]["value"]
        after = result["protected"]["value"]

        result["change_pp"] = (
            round((after - before) * 100, 4)
            if before is not None and after is not None
            else None
        )

        return result

    def analyze(
        self,
        subset: str = "all"
    ) -> dict:
        """Комплексный анализ эксперимента."""

        attempts = self.load_attempts()

        latest = self.get_latest_results(
            attempts
        )

        selected_ids = self.get_subset_ids(
            subset
        )

        paired_ids = self.get_paired_ids(
            latest,
            selected_ids
        )

        return {
            "experiment_id": self.experiment_id,
            "model": self.metadata["model"],
            "subset": subset,
            "expected_scenarios": len(selected_ids),
            "paired_scenarios": len(paired_ids),

            "complete": (
                paired_ids == selected_ids
            ),

            "pair_coverage": self.ratio(
                len(paired_ids),
                len(selected_ids)
            ),

            "progress": {
                mode: self.get_mode_statistics(
                    latest,
                    attempts,
                    selected_ids,
                    mode
                )
                for mode in self.MODES
            },

            "security": self.analyze_outcomes(
                latest,
                selected_ids,
                paired_ids,
                normal=False
            ),

            "normal": self.analyze_outcomes(
                latest,
                selected_ids,
                paired_ids,
                normal=True
            ),

            "risks": self.analyze_risks(
                latest,
                selected_ids,
                paired_ids
            )
        }

    def save_report(self, report: dict):
        """Сохранение экспериментального отчёта."""

        subset = report["subset"]

        json_path = (
            self.output_dir / f"report_{subset}.json"
        )

        csv_path = (
            self.output_dir / f"risks_{subset}.csv"
        )

        json_path.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

        rows = report["risks"]

        if rows:

            with csv_path.open(
                "w",
                encoding="utf-8-sig",
                newline=""
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=list(rows[0].keys())
                )

                writer.writeheader()
                writer.writerows(rows)

        return json_path, csv_path