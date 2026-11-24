from src.data_loader import load_fmea_config


class FMEAModel:

    def __init__(self):

        self.config = load_fmea_config()

    def calculate_asr(
        self,
        successful_attacks: int,
        valid_tests: int
    ) -> float:

        """Расчёт доли успешных атак."""

        if valid_tests <= 0:
            raise ValueError(
                "Нет корректных результатов тестирования"
            )

        if not 0 <= successful_attacks <= valid_tests:
            raise ValueError(
                "Некорректное количество успешных атак"
            )

        return successful_attacks / valid_tests

    def calculate_occurrence(self, asr: float) -> int:

        """Определение вероятности возникновения риска."""

        if not 0 <= asr <= 1:
            raise ValueError("ASR должен быть от 0 до 1")

        thresholds = self.config["occurrence_thresholds"]

        for threshold in thresholds:

            if asr <= threshold["max_asr"]:
                return threshold["score"]

        raise ValueError("Не удалось определить оценку O")

    @staticmethod
    def calculate_rpn(
        severity: int,
        occurrence: int,
        detection: int
    ) -> int:

        """Расчёт приоритетного числа риска."""

        for score in (severity, occurrence, detection):

            if not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(
                    "Оценка должна быть целым числом от 1 до 5"
                )

        return severity * occurrence * detection

    def classify_risk(self, rpn: int) -> str:

        """Определение уровня риска."""

        if not 1 <= rpn <= 125:
            raise ValueError("Некорректное значение RPN")

        for item in self.config["risk_levels"]:

            if rpn <= item["max_rpn"]:
                return item["level"]

        raise ValueError("Не удалось определить уровень риска")

    def assess(
        self,
        risk_id: str,
        successful_attacks: int,
        valid_tests: int
    ) -> dict:

        """Комплексная оценка риска методом FMEA."""

        parameters = self.config[
            "risk_parameters"
        ][risk_id]

        severity = parameters["severity"]
        detection = parameters["detection"]

        asr = self.calculate_asr(
            successful_attacks,
            valid_tests
        )

        occurrence = self.calculate_occurrence(asr)

        rpn = self.calculate_rpn(
            severity,
            occurrence,
            detection
        )

        level = self.classify_risk(rpn)

        return {
            "risk_id": risk_id,
            "successful_attacks": successful_attacks,
            "valid_tests": valid_tests,
            "asr": round(asr, 6),
            "severity": severity,
            "occurrence": occurrence,
            "detection": detection,
            "rpn": rpn,
            "risk_level": level
        }