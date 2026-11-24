import unittest

from src.data_loader import load_test_cases
from src.evaluator import ResponseEvaluator


class TestDataset(unittest.TestCase):

    def setUp(self):

        self.cases = load_test_cases()
        self.evaluator = ResponseEvaluator()

    def test_dataset_size(self):
        """Проверка количества сценариев."""

        self.assertEqual(len(self.cases), 100)

    def test_marker_detection(self):
        """Проверка распознавания контрольных маркеров."""

        for case in self.cases:

            expected = (
                "PASS"
                if case["check_type"] == "required"
                else "FAIL"
            )

            for marker in case["markers"]:

                with self.subTest(
                    test_id=case["test_id"],
                    marker=marker
                ):

                    response = f"Результат: {marker}"

                    result = self.evaluator.evaluate(
                        case,
                        response
                    )

                    self.assertEqual(
                        result["status"],
                        expected
                    )

    def test_response_without_markers(self):
        """Проверка ответа без контрольных маркеров."""

        for case in self.cases:

            with self.subTest(
                test_id=case["test_id"]
            ):

                response = (
                    "Извините, информация недоступна."
                )

                result = self.evaluator.evaluate(
                    case,
                    response
                )

                expected = (
                    "FAIL"
                    if case["check_type"] == "required"
                    else "PASS"
                )

                self.assertEqual(
                    result["status"],
                    expected
                )

    def test_empty_responses(self):
        """Проверка обработки пустых ответов."""

        for case in self.cases:

            with self.subTest(
                test_id=case["test_id"]
            ):

                result = self.evaluator.evaluate(
                    case,
                    ""
                )

                self.assertEqual(
                    result["status"],
                    "ERROR"
                )

    def test_attack_success(self):
        """Проверка определения успешности атаки."""

        for case in self.cases:

            with self.subTest(
                test_id=case["test_id"]
            ):

                response = (
                    f"Результат: {case['markers'][0]}"
                )

                result = self.evaluator.evaluate(
                    case,
                    response
                )

                if case["risk_id"] == "NORMAL":

                    self.assertIsNone(
                        result["attack_success"]
                    )

                else:

                    self.assertIs(
                        result["attack_success"],
                        True
                    )


if __name__ == "__main__":
    unittest.main()