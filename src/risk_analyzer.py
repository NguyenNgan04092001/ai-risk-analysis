import csv
from pathlib import Path

from src.data_loader import load_risk_catalog
from src.fmea import FMEAModel


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


class RiskAnalyzer:

    def __init__(self):

        self.fmea = FMEAModel()
        self.risks = load_risk_catalog()

    @staticmethod
    def load_results(filename: str) -> list:
        """Загрузка результатов тестирования."""

        file_path = RESULTS_DIR / filename

        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            return list(csv.DictReader(file))

    @staticmethod
    def get_statistics(
        results: list,
        risk_id: str
    ) -> dict:

        """Расчёт статистики по категории риска."""

        selected = [
            row for row in results
            if row["risk_id"] == risk_id
        ]

        valid = [
            row for row in selected
            if row["status"] in ("PASS", "FAIL")
        ]

        successful_attacks = sum(
            row["attack_success"].lower() == "true"
            for row in valid
        )

        errors = sum(
            row["status"] == "ERROR"
            for row in selected
        )

        return {
            "total": len(selected),
            "valid": len(valid),
            "successful_attacks": successful_attacks,
            "errors": errors
        }

    def analyze_risk(
        self,
        risk: dict,
        baseline: list,
        protected: list
    ) -> dict:

        """Сравнительный анализ одного риска."""

        risk_id = risk["risk_id"]

        before = self.get_statistics(
            baseline,
            risk_id
        )

        after = self.get_statistics(
            protected,
            risk_id
        )

        result = {
            "risk_id": risk_id,
            "risk_name": risk["name"],
            "owasp_id": risk["owasp_id"],
            "tests_before": before["total"],
            "tests_after": after["total"],
            "valid_before": before["valid"],
            "valid_after": after["valid"],
            "errors_before": before["errors"],
            "errors_after": after["errors"],
            "attacks_before": before["successful_attacks"],
            "attacks_after": after["successful_attacks"],
            "asr_before": None,
            "asr_after": None,
            "severity": None,
            "detection": None,
            "occurrence_before": None,
            "occurrence_after": None,
            "rpn_before": None,
            "rpn_after": None,
            "level_before": None,
            "level_after": None,
            "rpn_reduction_percent": None,
            "evaluation_status": "Неполные данные"
        }

        # Проверка наличия корректных результатов
        if before["valid"] == 0 or after["valid"] == 0:
            return result

        initial = self.fmea.assess(
            risk_id,
            before["successful_attacks"],
            before["valid"]
        )

        residual = self.fmea.assess(
            risk_id,
            after["successful_attacks"],
            after["valid"]
        )

        reduction = (
            (initial["rpn"] - residual["rpn"])
            / initial["rpn"] * 100
        )

        # Проверка сопоставимости тестовых сценариев
        before_ids = sorted(
            row["test_id"] for row in baseline
            if row["risk_id"] == risk_id
            and row["status"] in ("PASS", "FAIL")
        )

        after_ids = sorted(
            row["test_id"] for row in protected
            if row["risk_id"] == risk_id
            and row["status"] in ("PASS", "FAIL")
        )

        complete = (
            before["errors"] == 0
            and after["errors"] == 0
            and before["valid"] == before["total"]
            and after["valid"] == after["total"]
            and before_ids == after_ids
        )

        result.update({
            "asr_before": initial["asr"],
            "asr_after": residual["asr"],
            "severity": initial["severity"],
            "detection": initial["detection"],
            "occurrence_before": initial["occurrence"],
            "occurrence_after": residual["occurrence"],
            "rpn_before": initial["rpn"],
            "rpn_after": residual["rpn"],
            "level_before": initial["risk_level"],
            "level_after": residual["risk_level"],
            "rpn_reduction_percent": round(reduction, 2),
            "evaluation_status": (
                "Завершена" if complete
                else "Предварительная"
            )
        })

        return result

    def analyze_all(self) -> list:

        """Анализ всех категорий риска."""

        baseline = self.load_results("baseline.csv")
        protected = self.load_results("protected.csv")

        report = [
            self.analyze_risk(
                risk,
                baseline,
                protected
            )
            for risk in self.risks
        ]

        # Сортировка по исходному уровню риска
        report.sort(
            key=lambda row: (
                row["rpn_before"]
                if row["rpn_before"] is not None
                else -1
            ),
            reverse=True
        )

        return report

    @staticmethod
    def save_report(report: list):

        """Сохранение отчёта об оценке рисков."""

        if not report:
            raise ValueError("Отчёт не содержит данных")

        output_path = RESULTS_DIR / "risk_report.csv"

        with output_path.open(
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=list(report[0].keys())
            )

            writer.writeheader()
            writer.writerows(report)

        return output_path