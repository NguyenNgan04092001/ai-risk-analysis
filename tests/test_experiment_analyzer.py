import unittest

from src.experiment_analyzer import ExperimentAnalyzer
from src.risk_analyzer import RiskAnalyzer


class TestExperimentAnalyzer(unittest.TestCase):

    def setUp(self):

        self.analyzer = ExperimentAnalyzer.__new__(
            ExperimentAnalyzer
        )

        self.analyzer.experiment_id = "test_experiment"

        self.analyzer.metadata = {
            "model": "test-model"
        }

        self.analyzer.analyzer = RiskAnalyzer()

        self.analyzer.cases_by_id = {
            "T004": {
                "risk_id": "R02",
                "customer_id": "C001",
                "prompt": "Тестовый запрос"
            },
            "T035": {
                "risk_id": "R02",
                "customer_id": "C001",
                "prompt": "Тестовый запрос"
            },
            "T079": {
                "risk_id": "NORMAL",
                "customer_id": "C001",
                "prompt": "Тестовый запрос"
            }
        }

    def make_result(self, mode, test_id, status):

        case = self.analyzer.cases_by_id[test_id]

        return {
            "mode": mode,
            "test_id": test_id,
            "risk_id": case["risk_id"],
            "customer_id": case["customer_id"],
            "prompt": case["prompt"],
            "status": status,
            "model": "test-model",
            "attack_success": (
                None
                if status == "ERROR"
                or case["risk_id"] == "NORMAL"
                else status == "FAIL"
            )
        }

    def test_subsets(self):
        """Проверка разделения набора данных."""

        self.assertEqual(
            self.analyzer.get_subset_ids("all"),
            {"T004", "T035", "T079"}
        )

        self.assertEqual(
            self.analyzer.get_subset_ids("pilot"),
            {"T004"}
        )

        self.assertEqual(
            self.analyzer.get_subset_ids("new"),
            {"T035", "T079"}
        )

    def test_empty_ratio(self):
        """Отсутствие данных не считается нулевой оценкой."""

        self.assertIsNone(
            self.analyzer.ratio(0, 0)
        )

    def test_paired_results(self):
        """Проверка сопоставления пар сценариев."""

        attempts = [
            self.make_result(
                "baseline", "T004", "FAIL"
            ),
            self.make_result(
                "protected", "T004", "PASS"
            ),
            self.make_result(
                "baseline", "T035", "PASS"
            )
        ]

        latest = self.analyzer.get_latest_results(
            attempts
        )

        paired = self.analyzer.get_paired_ids(
            latest,
            self.analyzer.get_subset_ids()
        )

        self.assertEqual(paired, {"T004"})

    def test_error_exclusion(self):
        """Исключение технических ошибок."""

        attempts = [
            self.make_result(
                "baseline", "T004", "PASS"
            ),
            self.make_result(
                "protected", "T004", "ERROR"
            )
        ]

        latest = self.analyzer.get_latest_results(
            attempts
        )

        paired = self.analyzer.get_paired_ids(
            latest,
            {"T004"}
        )

        self.assertEqual(len(paired), 0)

    def test_retry_result(self):
        """Успешный результат после технической ошибки."""

        attempts = [
            self.make_result(
                "baseline", "T004", "ERROR"
            ),
            self.make_result(
                "baseline", "T004", "PASS"
            )
        ]

        latest = self.analyzer.get_latest_results(
            attempts
        )

        self.assertEqual(
            latest[("baseline", "T004")]["status"],
            "PASS"
        )

    def test_duplicate_completed(self):
        """Запрет повторных завершённых результатов."""

        row = self.make_result(
            "baseline", "T004", "PASS"
        )

        with self.assertRaises(ValueError):

            self.analyzer.get_latest_results(
                [row, row.copy()]
            )

    def test_model_mismatch(self):
        """Проверка соответствия модели."""

        row = self.make_result(
            "baseline", "T004", "PASS"
        )

        row["model"] = "another-model"

        with self.assertRaises(ValueError):

            self.analyzer.validate_result(row)

    def test_security_metrics(self):
        """Проверка расчёта ASR."""

        attempts = [
            self.make_result(
                "baseline", "T004", "FAIL"
            ),
            self.make_result(
                "protected", "T004", "PASS"
            )
        ]

        latest = self.analyzer.get_latest_results(
            attempts
        )

        report = self.analyzer.analyze_outcomes(
            latest,
            {"T004", "T035"},
            {"T004"},
            normal=False
        )

        self.assertEqual(
            report["baseline"]["value"],
            1.0
        )

        self.assertEqual(
            report["protected"]["value"],
            0.0
        )

        self.assertEqual(
            report["pair_coverage"],
            0.5
        )

    def test_normal_accuracy(self):
        """Проверка точности обычных запросов."""

        attempts = [
            self.make_result(
                "baseline", "T079", "PASS"
            ),
            self.make_result(
                "protected", "T079", "FAIL"
            )
        ]

        latest = self.analyzer.get_latest_results(
            attempts
        )

        report = self.analyzer.analyze_outcomes(
            latest,
            {"T079"},
            {"T079"},
            normal=True
        )

        self.assertEqual(
            report["baseline"]["value"],
            1.0
        )

        self.assertEqual(
            report["protected"]["value"],
            0.0
        )

    def test_preliminary_fmea(self):
        """Проверка неполного парного анализа FMEA."""

        attempts = [
            self.make_result(
                "baseline", "T004", "FAIL"
            ),
            self.make_result(
                "protected", "T004", "PASS"
            )
        ]

        latest = self.analyzer.get_latest_results(
            attempts
        )

        report = self.analyzer.analyze_risks(
            latest,
            {"T004", "T035"},
            {"T004"}
        )

        risk = next(
            row for row in report
            if row["risk_id"] == "R02"
        )

        self.assertEqual(
            risk["expected_scenarios"], 2
        )

        self.assertEqual(
            risk["paired_scenarios"], 1
        )

        self.assertEqual(
            risk["evaluation_status"],
            "Предварительная"
        )

        self.assertEqual(
            risk["rpn_before"], 75
        )

        self.assertEqual(
            risk["rpn_after"], 15
        )


if __name__ == "__main__":
    unittest.main()