from src.risk_analyzer import RiskAnalyzer


def main():

    analyzer = RiskAnalyzer()

    report = analyzer.analyze_all()

    print("\nРЕЗУЛЬТАТЫ АНАЛИЗА РИСКОВ")
    print("=" * 70)

    for risk in report:

        print("\nРиск:", risk["risk_id"])
        print("Название:", risk["risk_name"])
        print("OWASP:", risk["owasp_id"])

        print(
            "Корректные тесты до защиты:",
            risk["valid_before"]
        )

        print(
            "Корректные тесты после защиты:",
            risk["valid_after"]
        )

        if risk["asr_before"] is None:

            print("Недостаточно данных")
            continue

        print(
            "ASR до защиты:",
            f"{risk['asr_before'] * 100:.2f}%"
        )

        print(
            "ASR после защиты:",
            f"{risk['asr_after'] * 100:.2f}%"
        )

        print(
            "Исходный RPN:",
            risk["rpn_before"],
            f"({risk['level_before']})"
        )

        print(
            "Остаточный RPN:",
            risk["rpn_after"],
            f"({risk['level_after']})"
        )

        print(
            "Снижение RPN:",
            f"{risk['rpn_reduction_percent']:.2f}%"
        )

        print(
            "Статус оценки:",
            risk["evaluation_status"]
        )

        print("-" * 70)

    output_path = analyzer.save_report(report)

    print("\nОтчёт сохранён:", output_path)


if __name__ == "__main__":
    main()