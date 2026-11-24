import argparse
from collections import Counter

from src.attack_runner import AttackRunner


def parse_args():
    """Обработка аргументов командной строки."""

    parser = argparse.ArgumentParser(
        description=(
            "Автоматизированное тестирование "
            "безопасности банковского ИИ-ассистента"
        )
    )

    parser.add_argument(
        "--mode",
        choices=["baseline", "protected", "both"],
        default="baseline",
        help="Режим тестирования"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=4.0,
        help="Задержка между запросами в секундах"
    )

    args = parser.parse_args()

    if args.delay < 0:
        parser.error("Задержка не может быть отрицательной")

    return args


def run_experiment(mode: str, delay: float):

    runner = AttackRunner(
        mode=mode,
        delay=delay
    )

    results = runner.run_all()

    statistics = Counter(
        result["status"]
        for result in results
    )

    print("\nИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    print("Режим:", mode)
    print("Всего сценариев:", len(results))
    print("Успешные проверки:", statistics["PASS"])
    print("Неуспешные проверки:", statistics["FAIL"])
    print("Ошибки выполнения:", statistics["ERROR"])
    print("=" * 50)

    return results


def main():

    args = parse_args()

    if args.mode == "both":

        run_experiment("baseline", args.delay)
        run_experiment("protected", args.delay)

    else:

        run_experiment(args.mode, args.delay)


if __name__ == "__main__":
    main()