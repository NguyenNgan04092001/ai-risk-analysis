import json

from collections import Counter
from src.data_loader import load_test_cases


def main():

    cases = load_test_cases()

    errors = []
    warnings = []

    required_fields = {
        "test_id",
        "risk_id",
        "description",
        "customer_id",
        "prompt",
        "expected_behavior",
        "check_type",
        "markers"
    }

    ids = Counter()
    prompts = Counter()

    for case in cases:

        test_id = case.get("test_id", "UNKNOWN")

        # Проверка обязательных полей
        missing = required_fields - set(case.keys())

        if missing:

            errors.append(
                f"{test_id}: отсутствуют поля {missing}"
            )

            continue

        ids[test_id] += 1

        prompt = case["prompt"].strip().casefold()

        prompts[(case["customer_id"], prompt)] += 1

        # Проверка типа сценария
        expected_type = (
            "required"
            if case["risk_id"] == "NORMAL"
            else "forbidden"
        )

        if case["check_type"] != expected_type:

            errors.append(
                f"{test_id}: неверный тип проверки"
            )

        # Проверка контрольных маркеров
        markers = case["markers"]

        if not isinstance(markers, list) or not markers:

            errors.append(
                f"{test_id}: отсутствуют маркеры"
            )

        else:

            for marker in markers:

                if not isinstance(marker, str):

                    errors.append(
                        f"{test_id}: маркер не является строкой"
                    )

                elif not marker.strip():

                    errors.append(
                        f"{test_id}: пустой маркер"
                    )

                elif len(marker.strip()) < 3 and marker.strip() != "$2":

                    warnings.append(
                        f"{test_id}: короткий маркер {marker!r}"
                    )

        # Проверка идентификатора клиента
        if case["customer_id"] not in ("C001", "C002"):

            errors.append(
                f"{test_id}: неизвестный клиент"
            )

        if not prompt:

            errors.append(
                f"{test_id}: пустой запрос"
            )

    # Проверка дубликатов
    for test_id, count in ids.items():

        if count > 1:

            errors.append(
                f"Повторяющийся ID: {test_id}"
            )

    for (customer_id, prompt), count in prompts.items():

        if count > 1:

            warnings.append(
                f"Повторяющийся запрос: {customer_id} | {prompt}"
            )

    distribution = Counter(
        case.get("risk_id") for case in cases
    )

    if len(cases) != 100:

        errors.append(
            "Количество сценариев не равно 100"
        )

    expected_distribution = {
        "R01": 25,
        "R02": 25,
        "R03": 25,
        "NORMAL": 25
    }

    if distribution != expected_distribution:

        errors.append(
            "Некорректное распределение сценариев"
        )

    print("=" * 60)
    print("ПРОВЕРКА НАБОРА ТЕСТОВЫХ СЦЕНАРИЕВ")
    print("=" * 60)

    print("Количество сценариев:", len(cases))

    print("\nРаспределение по категориям:")

    for risk_id, count in distribution.items():

        print(f"{risk_id}: {count}")

    print("\nРаспределение по клиентам:")

    customers = Counter(
        case.get("customer_id") for case in cases
    )

    for customer_id, count in customers.items():

        print(f"{customer_id}: {count}")

    print("\nКоличество ошибок:", len(errors))

    for error in errors:
        print("ERROR:", error)

    print("\nКоличество предупреждений:", len(warnings))

    for warning in warnings:
        print("WARNING:", warning)

    print("\nРезультат:", "OK" if not errors else "FAILED")

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()