import argparse
import csv
import json
import shutil
import time

from pathlib import Path
from datetime import datetime

from src.attack_runner import AttackRunner


ROOT = Path(__file__).resolve().parent


def retry_errors(mode: str):

    file_path = ROOT / "results" / f"{mode}.csv"

    if not file_path.exists():
        print("Файл результатов не найден")
        return

    # Загрузка предыдущих результатов
    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    error_rows = [
        row for row in rows
        if row["status"] == "ERROR"
    ]

    print("Режим:", mode)
    print("Количество ошибок:", len(error_rows))

    if not error_rows:
        print("Ошибки не обнаружены")
        return

    # Создание резервной копии
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = ROOT / "results" / (
        f"{mode}_backup_{timestamp}.csv"
    )

    shutil.copy2(file_path, backup_path)

    runner = AttackRunner(
        mode=mode,
        delay=4.0
    )

    cases = {
        case["test_id"]: case
        for case in runner.test_cases
    }

    # Повторное выполнение ошибочных сценариев
    for index, row in enumerate(rows):

        if row["status"] != "ERROR":
            continue

        test_id = row["test_id"]

        print("\nПовторный тест:", test_id)

        result = runner.run_case(cases[test_id])

        result["matched_markers"] = json.dumps(
            result["matched_markers"],
            ensure_ascii=False
        )

        # Обновление результата сценария
        rows[index] = result

        print("Статус:", result["status"])
        print("Ответ:", result["response"])
        print("Причина:", result["reason"])

        time.sleep(runner.delay)

    # Сохранение обновлённых результатов
    temp_path = file_path.with_suffix(".tmp")

    with temp_path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    temp_path.replace(file_path)

    remaining = sum(
        row["status"] == "ERROR"
        for row in rows
    )

    print("\nПовторное тестирование завершено")
    print("Оставшиеся ошибки:", remaining)
    print("Резервная копия:", backup_path)
    print("Результаты сохранены:", file_path)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["baseline", "protected"],
        default="protected"
    )

    args = parser.parse_args()

    retry_errors(args.mode)


if __name__ == "__main__":
    main()