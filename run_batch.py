import argparse
import re

from pprint import pprint

from src.experiment import ExperimentManager


def main():

    parser = argparse.ArgumentParser(
        description="Управление экспериментами"
    )

    parser.add_argument(
        "--id",
        default="experiment_001"
    )

    parser.add_argument(
        "--max-requests",
        type=int,
        default=40
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=4.0
    )

    parser.add_argument(
        "--status",
        action="store_true"
    )

    args = parser.parse_args()

    if args.max_requests <= 0:
        parser.error(
            "Количество запросов должно быть больше нуля"
        )

    if args.delay < 4:
        parser.error(
            "Интервал должен быть не менее 4 секунд"
        )

    if not re.fullmatch(
        r"[a-zA-Z0-9_-]+", args.id
    ):
        parser.error(
            "Некорректный идентификатор эксперимента"
        )

    manager = ExperimentManager(
        experiment_id=args.id,
        delay=args.delay
    )

    if args.status:

        print("СТАТУС ЭКСПЕРИМЕНТА")
        pprint(manager.get_progress())

    else:

        progress = manager.run(
            max_requests=args.max_requests
        )

        print("\nИТОГИ ЭТАПА")
        pprint(progress)


if __name__ == "__main__":
    main()