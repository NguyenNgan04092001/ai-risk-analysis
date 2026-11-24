import unittest

from src.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzer(unittest.TestCase):

    def setUp(self):

        self.analyzer = RiskAnalyzer()

        self.risk = {
            "risk_id": "R02",
            "name": "Раскрытие конфиденциальной информации",
            "owasp_id": "LLM02:2025"
        }

        # Синтетические данные для модульного тестирования
        self.baseline = [
            {
                "test_id": "T004",
                "risk_id": "R02",
                "status": "FAIL",
                "attack_success": "True"
            },
            {
                "test_id": "T005",
                "risk_id": "R02",
                "status": "FAIL",
                "attack_success": "True"
            },
            {
                "test_id": "T006",
                "risk_id": "R02",
                "status": "PASS",
                "attack_success": "False"
            }
        ]

        self.protected = [
            {
                "test_id": test_id,
                "risk_id": "R02",
                "status": "PASS",
                "attack_success": "False"
            }
            for test_id in ["T004", "T005", "T006"]
        ]

    def test_statistics(self):
        """Проверка статистики тестирования."""

        result = self.analyzer.get_statistics(
            self.baseline,
            "R02"
        )

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["valid"], 3)
        self.assertEqual(result["successful_attacks"], 2)
        self.assertEqual(result["errors"], 0)

    def test_complete_analysis(self):
        """Проверка полного анализа риска."""

        result = self.analyzer.analyze_risk(
            self.risk,
            self.baseline,
            self.protected
        )

        self.assertAlmostEqual(
            result["asr_before"],
            2 / 3,
            places=5
        )

        self.assertEqual(result["asr_after"], 0)
        self.assertEqual(result["rpn_before"], 60)
        self.assertEqual(result["rpn_after"], 15)

        self.assertEqual(
            result["evaluation_status"],
            "Завершена"
        )

    def test_rpn_reduction(self):
        """Проверка снижения RPN."""

        result = self.analyzer.analyze_risk(
            self.risk,
            self.baseline,
            self.protected
        )

        self.assertEqual(
            result["rpn_reduction_percent"],
            75.0
        )

    def test_error_handling(self):
        """Исключение технических ошибок из расчёта ASR."""

        rows = [
            row.copy()
            for row in self.protected
        ]

        rows[0]["status"] = "ERROR"
        rows[0]["attack_success"] = ""

        result = self.analyzer.get_statistics(
            rows,
            "R02"
        )

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["valid"], 2)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["successful_attacks"], 0)

    def test_preliminary_analysis(self):
        """Проверка предварительной оценки."""

        result = self.analyzer.analyze_risk(
            self.risk,
            self.baseline,
            self.protected[:2]
        )

        self.assertEqual(
            result["evaluation_status"],
            "Предварительная"
        )

    def test_missing_data(self):
        """Проверка отсутствующих результатов."""

        result = self.analyzer.analyze_risk(
            self.risk,
            self.baseline,
            []
        )

        self.assertIsNone(result["rpn_after"])

        self.assertEqual(
            result["evaluation_status"],
            "Неполные данные"
        )


if __name__ == "__main__":
    unittest.main()