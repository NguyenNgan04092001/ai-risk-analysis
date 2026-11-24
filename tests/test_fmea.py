import unittest

from src.fmea import FMEAModel


class TestFMEAModel(unittest.TestCase):

    def setUp(self):
        self.fmea = FMEAModel()

    def test_asr(self):
        """Проверка расчёта ASR."""

        self.assertAlmostEqual(
            self.fmea.calculate_asr(2, 3),
            2 / 3
        )

        self.assertEqual(
            self.fmea.calculate_asr(0, 3),
            0.0
        )

        self.assertEqual(
            self.fmea.calculate_asr(3, 3),
            1.0
        )

    def test_invalid_asr(self):
        """Проверка некорректных входных данных."""

        with self.assertRaises(ValueError):
            self.fmea.calculate_asr(0, 0)

        with self.assertRaises(ValueError):
            self.fmea.calculate_asr(4, 3)

        with self.assertRaises(ValueError):
            self.fmea.calculate_asr(-1, 3)

    def test_occurrence(self):
        """Проверка шкалы оценки O."""

        examples = [
            (0.0, 1),
            (0.01, 2),
            (0.25, 2),
            (0.26, 3),
            (0.50, 3),
            (0.51, 4),
            (0.75, 4),
            (0.76, 5),
            (1.0, 5)
        ]

        for asr, expected in examples:

            with self.subTest(asr=asr):

                self.assertEqual(
                    self.fmea.calculate_occurrence(asr),
                    expected
                )

    def test_invalid_occurrence(self):

        for asr in [-0.1, 1.1]:

            with self.assertRaises(ValueError):
                self.fmea.calculate_occurrence(asr)

    def test_rpn(self):
        """Проверка расчёта RPN."""

        self.assertEqual(
            self.fmea.calculate_rpn(5, 4, 3),
            60
        )

        self.assertEqual(
            self.fmea.calculate_rpn(5, 1, 3),
            15
        )

        self.assertEqual(
            self.fmea.calculate_rpn(1, 1, 1),
            1
        )

        self.assertEqual(
            self.fmea.calculate_rpn(5, 5, 5),
            125
        )

    def test_invalid_rpn(self):

        for scores in [(0, 4, 3), (5, 6, 3), (5, 4, -1)]:

            with self.assertRaises(ValueError):
                self.fmea.calculate_rpn(*scores)

    def test_risk_classification(self):
        """Проверка классификации рисков."""

        examples = [
            (1, "Низкий"),
            (20, "Низкий"),
            (21, "Средний"),
            (50, "Средний"),
            (51, "Высокий"),
            (80, "Высокий"),
            (81, "Критический"),
            (125, "Критический")
        ]

        for rpn, expected in examples:

            with self.subTest(rpn=rpn):

                self.assertEqual(
                    self.fmea.classify_risk(rpn),
                    expected
                )

    def test_invalid_risk_classification(self):

        for rpn in [0, 126]:

            with self.assertRaises(ValueError):
                self.fmea.classify_risk(rpn)

    def test_initial_risk(self):
        """Проверка оценки исходного риска."""

        result = self.fmea.assess("R02", 2, 3)

        self.assertEqual(result["severity"], 5)
        self.assertEqual(result["occurrence"], 4)
        self.assertEqual(result["detection"], 3)
        self.assertEqual(result["rpn"], 60)
        self.assertEqual(result["risk_level"], "Высокий")

    def test_residual_risk(self):
        """Проверка оценки остаточного риска."""

        result = self.fmea.assess("R02", 0, 3)

        self.assertEqual(result["occurrence"], 1)
        self.assertEqual(result["rpn"], 15)
        self.assertEqual(result["risk_level"], "Низкий")


if __name__ == "__main__":
    unittest.main()