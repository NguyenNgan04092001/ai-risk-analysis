import argparse

from src.experiment_analyzer import ExperimentAnalyzer


def format_percent(value):

    if value is None:
        return "Нет данных"

    return f"{value * 100:.2f}%"


def main():

    parser = argparse.ArgumentParser(
        description="Анализ результатов эксперимента"
    )

    parser.add_argument(
        "--id",
        default="experiment_002"
    )

    parser.add_argument(
        "--subset",
        choices=["all", "new", "pilot"],
        default="all"
    )

    args = parser.parse_args()

    analyzer = ExperimentAnalyzer(
        experiment_id=args.id
    )

    report = analyzer.analyze(
        subset=args.subset
    )

    print("=" * 70)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ ЭКСПЕРИМЕНТА")
    print("=" * 70)

    print("Эксперимент:", report["experiment_id"])
    print("Модель:", report["model"])
    print("Поднабор:", report["subset"])

    print(
        "Количество сценариев:",
        report["expected_scenarios"]
    )

    print(
        "Завершённые пары:",
        report["paired_scenarios"]
    )

    print(
        "Полнота эксперимента:",
        format_percent(report["pair_coverage"])
    )

    print("\nСТАТИСТИКА ВЫПОЛНЕНИЯ")

    for mode, stats in report["progress"].items():

        print(f"\n{mode.upper()}")

        print(
            "Завершено:",
            stats["completed"],
            "/",
            stats["expected"]
        )

        print(
            "Количество попыток:",
            stats["attempts"]
        )

        print(
            "Технические ошибки:",
            stats["error_attempts"]
        )

        print(
            "Доля технических ошибок:",
            format_percent(stats["error_rate"])
        )

    print("\nОБЩАЯ ОЦЕНКА БЕЗОПАСНОСТИ")

    security = report["security"]

    print(
        "ASR до защиты:",
        format_percent(
            security["baseline"]["value"]
        )
    )

    print(
        "ASR после защиты:",
        format_percent(
            security["protected"]["value"]
        )
    )

    print("\nОБЫЧНЫЕ ЗАПРОСЫ")

    normal = report["normal"]

    print(
        "Точность до защиты:",
        format_percent(
            normal["baseline"]["value"]
        )
    )

    print(
        "Точность после защиты:",
        format_percent(
            normal["protected"]["value"]
        )
    )

    print("\nОЦЕНКА РИСКОВ FMEA")

    for risk in report["risks"]:

        print("-" * 70)

        print(
            risk["risk_id"],
            "|",
            risk["risk_name"]
        )

        print(
            "Завершённые пары:",
            risk["paired_scenarios"],
            "/",
            risk["expected_scenarios"]
        )

        print(
            "ASR:",
            format_percent(risk["asr_before"]),
            "->",
            format_percent(risk["asr_after"])
        )

        print(
            "RPN:",
            risk["rpn_before"],
            "->",
            risk["rpn_after"]
        )

        print(
            "Статус:",
            risk["evaluation_status"]
        )

    paths = analyzer.save_report(report)

    print("\nСОХРАНЕНИЕ ОТЧЁТА")

    for path in paths:
        print(path)


if __name__ == "__main__":
    main()