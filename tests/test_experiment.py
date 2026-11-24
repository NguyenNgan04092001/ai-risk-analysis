import unittest
import json
import tempfile

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.experiment import ExperimentManager


class TestExperimentManager(unittest.TestCase):

    def setUp(self):

        # Временная директория для тестирования
        self.temp_dir = tempfile.TemporaryDirectory()

        self.addCleanup(self.temp_dir.cleanup)

        self.manager = ExperimentManager.__new__(
            ExperimentManager
        )

        self.manager.experiment_id = "test_experiment"
        self.manager.delay = 0

        self.manager.output_dir = Path(
            self.temp_dir.name
        )

        self.manager.results_file = (
            self.manager.output_dir / "results.jsonl"
        )

        self.manager.metadata_file = (
            self.manager.output_dir / "experiment.json"
        )

        self.manager.test_cases = [
            {
                "test_id": "T001",
                "risk_id": "R01"
            },
            {
                "test_id": "T002",
                "risk_id": "R02"
            }
        ]

        # Имитация работы LLM без обращения к API
        self.manager.runners = {
            "baseline": MagicMock(),
            "protected": MagicMock()
        }

        for mode, runner in self.manager.runners.items():

            runner.run_case.side_effect = (
                lambda case, mode=mode:
                self.make_result(
                    mode,
                    case["test_id"],
                    "PASS"
                )
            )

    def make_result(self, mode, test_id, status):

        return {
            "mode": mode,
            "test_id": test_id,
            "status": status,
            "response": (
                "Тестовый ответ"
                if status != "ERROR"
                else ""
            ),
            "reason": (
                "Техническая ошибка"
                if status == "ERROR"
                else "Проверка выполнена"
            ),
            "attack_success": (
                None if status == "ERROR"
                else status == "FAIL"
            ),
            "matched_markers": []
        }

    def test_empty_progress(self):
        """Проверка начального состояния."""

        progress = self.manager.get_progress()

        self.assertEqual(progress["total"], 4)
        self.assertEqual(progress["completed"], 0)
        self.assertEqual(progress["remaining"], 4)

    def test_save_and_load(self):
        """Проверка сохранения результатов."""

        result = self.make_result(
            "baseline", "T001", "PASS"
        )

        self.manager.save_result(result)

        loaded = self.manager.load_results()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0], result)

    def test_error_not_completed(self):
        """Техническая ошибка не считается завершением."""

        self.manager.save_result(
            self.make_result(
                "baseline", "T001", "ERROR"
            )
        )

        self.assertEqual(
            len(self.manager.get_completed()),
            0
        )

    def test_fail_is_completed(self):
        """Успешная атака считается завершённым тестом."""

        self.manager.save_result(
            self.make_result(
                "baseline", "T001", "FAIL"
            )
        )

        self.assertIn(
            ("baseline", "T001"),
            self.manager.get_completed()
        )

    def test_duplicate_results(self):
        """Проверка повторных результатов."""

        result = self.make_result(
            "baseline", "T001", "PASS"
        )

        self.manager.save_result(result)
        self.manager.save_result(result)

        self.assertEqual(
            self.manager.get_progress()["completed"],
            1
        )

    @patch("builtins.print")
    def test_request_limit(self, mock_print):
        """Проверка ограничения числа запросов."""

        progress = self.manager.run(max_requests=2)

        self.assertEqual(progress["completed"], 2)
        self.assertEqual(progress["remaining"], 2)

        total_calls = sum(
            runner.run_case.call_count
            for runner in self.manager.runners.values()
        )

        self.assertEqual(total_calls, 2)

    @patch("builtins.print")
    def test_resume_experiment(self, mock_print):
        """Проверка возобновления эксперимента."""

        self.manager.run(max_requests=2)

        progress = self.manager.run(max_requests=2)

        self.assertEqual(progress["completed"], 4)
        self.assertEqual(progress["remaining"], 0)
        self.assertEqual(progress["progress_percent"], 100)

        self.assertEqual(
            self.manager.runners[
                "baseline"
            ].run_case.call_count,
            2
        )

        self.assertEqual(
            self.manager.runners[
                "protected"
            ].run_case.call_count,
            2
        )

    @patch("builtins.print")
    def test_stop_on_error(self, mock_print):
        """Остановка при технической ошибке."""

        runner = self.manager.runners["baseline"]

        runner.run_case.side_effect = None

        runner.run_case.return_value = (
            self.make_result(
                "baseline", "T001", "ERROR"
            )
        )

        progress = self.manager.run(max_requests=4)

        self.assertEqual(progress["completed"], 0)

        self.assertEqual(
            runner.run_case.call_count,
            1
        )

        self.manager.runners[
            "protected"
        ].run_case.assert_not_called()

    @patch("builtins.print")
    def test_retry_error(self, mock_print):
        """Повторное выполнение после ошибки."""

        self.manager.save_result(
            self.make_result(
                "baseline", "T001", "ERROR"
            )
        )

        progress = self.manager.run(max_requests=1)

        self.assertEqual(progress["completed"], 1)

        self.assertIn(
            ("baseline", "T001"),
            self.manager.get_completed()
        )

    @patch("builtins.print")
    def test_csv_export(self, mock_print):
        """Проверка экспорта результатов в CSV."""

        self.manager.run(max_requests=4)

        self.assertTrue(
            (
                self.manager.output_dir / "baseline.csv"
            ).exists()
        )

        self.assertTrue(
            (
                self.manager.output_dir / "protected.csv"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()