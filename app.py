from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.bank_assistant import BankAssistant
from src.data_loader import load_risk_catalog
from src.risk_analyzer import RiskAnalyzer

from src.experiment_analyzer import ExperimentAnalyzer

from src.fmea import FMEAModel


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"


st.set_page_config(
    page_title="Система анализа рисков ИИ",
    page_icon="🛡️",
    layout="wide"
)


# Боковое меню
st.sidebar.title("AI Risk Analysis")

page = st.sidebar.radio(
    "Навигация",
    [
        "Главная",
        "Банковский ассистент",
        "Каталог рисков",
        "Тестирование безопасности",
        "Анализ рисков FMEA",
        "Экспериментальное исследование"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Методы: OWASP, ASR, FMEA"
)


# Главная страница
if page == "Главная":

    st.title("Система анализа рисков ИИ")

    st.subheader(
        "Модель анализа рисков использования "
        "нейросетевых моделей и генеративного "
        "искусственного интеллекта "
        "в финансовых сервисах"
    )

    st.write(
        "Система предназначена для выявления, "
        "оценки и сравнения рисков информационной "
        "безопасности банковского ИИ-ассистента."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Категории рисков", 3)

    col2.metric("Метод оценки", "FMEA")

    col3.metric("Метод защиты", "Guardrails")

    st.divider()

    st.subheader("Этапы анализа рисков")

    st.markdown("""
    1. Идентификация рисков на основе OWASP.
    2. Тестирование банковского ИИ-ассистента.
    3. Оценка исходных рисков методом FMEA.
    4. Применение дополнительных правил защиты.
    5. Оценка остаточных рисков.
    6. Сравнительный анализ результатов.
    """)

    st.info(
        "В системе используются только "
        "синтетические банковские данные."
    )


# Банковский ассистент
elif page == "Банковский ассистент":

    st.title("Банковский ИИ-ассистент")

    mode = st.radio(
        "Режим работы",
        ["baseline", "protected"],
        format_func=lambda value: {
            "baseline": "До защиты",
            "protected": "После защиты"
        }[value],
        horizontal=True
    )

    st.caption(
        "Авторизованный клиент: C001 — Alex Morgan "
        "(имитация авторизации)"
    )

    question = st.text_area(
        "Введите запрос",
        placeholder="Какой баланс моего счёта?"
    )

    if st.button("Отправить запрос", type="primary"):

        if not question.strip():

            st.warning("Введите запрос.")

        else:

            try:

                with st.spinner("Обработка запроса..."):

                    assistant = BankAssistant(mode=mode)

                    response = assistant.ask(
                        question=question,
                        customer_id="C001"
                    )

                st.subheader("Ответ ассистента")

                st.write(response)

                with st.expander("Метаданные ответа"):

                    st.json(assistant.llm.last_metadata)

            except Exception as e:

                st.error(f"Ошибка выполнения: {e}")


# Каталог рисков
elif page == "Каталог рисков":

    st.title("Каталог рисков информационной безопасности")

    st.caption(
        "OWASP Top 10 for LLM Applications 2025"
    )

    risks = load_risk_catalog()

    for risk in risks:

        with st.expander(
            f"{risk['risk_id']} — {risk['name']}",
            expanded=True
        ):

            st.write("**OWASP:**", risk["owasp_id"])

            st.write("**Описание:**", risk["description"])

            st.write("**Причина:**", risk["cause"])

            st.write("**Последствия:**", risk["impact"])

            st.write("**Защищаемый актив:**", risk["asset"])


# Результаты тестирования
elif page == "Тестирование безопасности":

    st.title("Тестирование информационной безопасности")

    st.info(
        "Пилотный эксперимент: 12 сценариев. "
        "Основной эксперимент доступен в отдельном разделе."
    )

    mode = st.radio(
        "Результаты тестирования",
        ["baseline", "protected"],
        format_func=lambda value: {
            "baseline": "До защиты",
            "protected": "После защиты"
        }[value],
        horizontal=True
    )

    file_path = RESULTS_DIR / f"{mode}.csv"

    if not file_path.exists():

        st.warning("Результаты тестирования не найдены.")

    else:

        df = pd.read_csv(file_path)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Всего тестов", len(df))

        col2.metric(
            "Тесты пройдены",
            int((df["status"] == "PASS").sum())
        )

        col3.metric(
            "Тесты не пройдены",
            int((df["status"] == "FAIL").sum())
        )

        col4.metric(
            "Ошибки",
            int((df["status"] == "ERROR").sum())
        )

        st.divider()

        # Фильтрация результатов
        categories = [
            "Все"
        ] + sorted(df["risk_id"].unique().tolist())

        selected_risk = st.selectbox(
            "Категория риска",
            categories
        )

        filtered = df.copy()

        if selected_risk != "Все":

            filtered = filtered[
                filtered["risk_id"] == selected_risk
            ]

        display_columns = {
            "test_id": "ID теста",
            "risk_id": "Риск",
            "description": "Описание",
            "status": "Статус",
            "duration": "Время, сек."
        }

        st.dataframe(
            filtered[list(display_columns.keys())].rename(
                columns=display_columns
            ),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Детали тестового сценария")

        if not filtered.empty:

            test_id = st.selectbox(
                "Выберите тест",
                filtered["test_id"].tolist()
            )

            row = filtered[
                filtered["test_id"] == test_id
            ].iloc[0]

            st.write("**Запрос:**", row["prompt"])

            st.write(
                "**Ожидаемое поведение:**",
                row["expected_behavior"]
            )

            st.write(
                "**Ответ модели:**",
                row["response"]
                if pd.notna(row["response"])
                else "Ответ отсутствует"
            )

            st.write("**Причина:**", row["reason"])

            if row["status"] == "PASS":

                st.success("Тест пройден")

            elif row["status"] == "FAIL":

                st.error("Тест не пройден")

            else:

                st.warning("Ошибка выполнения")

        st.download_button(
            "Скачать результаты CSV",
            data=file_path.read_bytes(),
            file_name=f"{mode}.csv",
            mime="text/csv"
        )


# Анализ рисков
elif page == "Анализ рисков FMEA":

    st.title("Оценка рисков методом FMEA")
    st.info("Пилотный эксперимент: результаты предварительной оценки.")

    st.latex(r"RPN = S \times O \times D")

    required_files = [
        RESULTS_DIR / "baseline.csv",
        RESULTS_DIR / "protected.csv"
    ]

    if not all(path.exists() for path in required_files):

        st.warning(
            "Необходимо провести тестирование "
            "до и после защиты."
        )

    else:

        analyzer = RiskAnalyzer()

        report = analyzer.analyze_all()

        analyzer.save_report(report)

        df = pd.DataFrame(report)

        if (df["evaluation_status"] != "Завершена").any():

            st.warning(
                "Некоторые результаты являются "
                "предварительными из-за неполных "
                "данных тестирования."
            )

        valid_df = df.dropna(
            subset=["rpn_before", "rpn_after"]
        )

        if valid_df.empty:

            st.warning(
                "Недостаточно данных для сравнения."
            )

        else:

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Количество рисков",
                len(df)
            )

            col2.metric(
                "Макс. исходный RPN",
                int(valid_df["rpn_before"].max())
            )

            col3.metric(
                "Макс. остаточный RPN",
                int(valid_df["rpn_after"].max())
            )

            # Диаграмма RPN
            rpn_data = valid_df.melt(
                id_vars=["risk_id"],
                value_vars=["rpn_before", "rpn_after"],
                var_name="mode",
                value_name="RPN"
            )

            rpn_data["mode"] = rpn_data["mode"].map({
                "rpn_before": "До защиты",
                "rpn_after": "После защиты"
            })

            fig_rpn = px.bar(
                rpn_data,
                x="risk_id",
                y="RPN",
                color="mode",
                barmode="group",
                text_auto=True,
                title=(
                    "Сравнение исходных "
                    "и остаточных рисков"
                ),
                labels={
                    "risk_id": "Категория риска",
                    "mode": "Режим"
                }
            )

            fig_rpn.update_yaxes(range=[0, 125])

            st.plotly_chart(
                fig_rpn,
                use_container_width=True
            )

            # Диаграмма ASR
            asr_data = valid_df.melt(
                id_vars=["risk_id"],
                value_vars=["asr_before", "asr_after"],
                var_name="mode",
                value_name="ASR"
            )

            asr_data["ASR"] *= 100

            asr_data["mode"] = asr_data["mode"].map({
                "asr_before": "До защиты",
                "asr_after": "После защиты"
            })

            fig_asr = px.bar(
                asr_data,
                x="risk_id",
                y="ASR",
                color="mode",
                barmode="group",
                text_auto=".1f",
                title="Доля успешных атак (ASR)",
                labels={
                    "risk_id": "Категория риска",
                    "mode": "Режим",
                    "ASR": "ASR, %"
                }
            )

            fig_asr.update_yaxes(range=[0, 100])

            st.plotly_chart(
                fig_asr,
                use_container_width=True
            )

        st.subheader("Таблица оценки рисков")

        columns = {
            "risk_id": "ID",
            "risk_name": "Название риска",
            "severity": "S",
            "detection": "D",
            "occurrence_before": "O до",
            "occurrence_after": "O после",
            "rpn_before": "RPN до",
            "rpn_after": "RPN после",
            "level_before": "Исходный уровень",
            "level_after": "Остаточный уровень",
            "rpn_reduction_percent": "Снижение RPN, %",
            "evaluation_status": "Статус оценки"
        }

        st.dataframe(
            df[list(columns.keys())].rename(columns=columns),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "ASR и RPN рассчитаны для экспериментальных "
            "условий и не отражают непосредственно "
            "вероятность инцидентов в реальном банке."
        )

        st.download_button(
            "Скачать отчёт об анализе рисков",
            data=(RESULTS_DIR / "risk_report.csv").read_bytes(),
            file_name="risk_report.csv",
            mime="text/csv"
        )

        # Анализ чувствительности модели FMEA
        st.divider()

        st.subheader(
            "Анализ чувствительности модели FMEA"
        )

        st.write(
            "Изменение параметров S и D позволяет "
            "оценить влияние экспертных оценок "
            "на приоритетное число риска."
        )

        available_risks = df.dropna(
            subset=[
                "occurrence_before",
                "occurrence_after"
            ]
        )

        if available_risks.empty:

            st.warning(
                "Недостаточно данных для анализа."
            )

        else:

            risk_names = dict(zip(
                available_risks["risk_id"],
                available_risks["risk_name"]
            ))

            selected_risk = st.selectbox(
                "Выберите категорию риска",
                list(risk_names.keys()),
                format_func=lambda value: (
                    f"{value} — {risk_names[value]}"
                ),
                key="sensitivity_risk"
            )

            risk_row = available_risks[
                available_risks["risk_id"] == selected_risk
            ].iloc[0]

            if risk_row["evaluation_status"] != "Завершена":

                st.warning(
                    "Оценка выбранного риска "
                    "является предварительной."
                )

            fmea = FMEAModel()

            default_s = int(risk_row["severity"])
            default_d = int(risk_row["detection"])

            s_key = f"severity_{selected_risk}"
            d_key = f"detection_{selected_risk}"

            # Восстановление исходных параметров
            if st.button("Восстановить исходные параметры"):

                st.session_state[s_key] = default_s
                st.session_state[d_key] = default_d

            col1, col2 = st.columns(2)

            with col1:

                severity = st.slider(
                    "Тяжесть последствий (S)",
                    min_value=1,
                    max_value=5,
                    value=default_s,
                    key=s_key
                )

            with col2:

                detection = st.slider(
                    "Сложность обнаружения (D)",
                    min_value=1,
                    max_value=5,
                    value=default_d,
                    key=d_key
                )

            occurrence_before = int(
                risk_row["occurrence_before"]
            )

            occurrence_after = int(
                risk_row["occurrence_after"]
            )

            rpn_before = fmea.calculate_rpn(
                severity,
                occurrence_before,
                detection
            )

            rpn_after = fmea.calculate_rpn(
                severity,
                occurrence_after,
                detection
            )

            level_before = fmea.classify_risk(
                rpn_before
            )

            level_after = fmea.classify_risk(
                rpn_after
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Исходный RPN",
                    rpn_before
                )

                st.write("Уровень риска:", level_before)
                st.caption(f"O = {occurrence_before}")

            with col2:

                st.metric(
                    "Остаточный RPN",
                    rpn_after
                )

                st.write("Уровень риска:", level_after)
                st.caption(f"O = {occurrence_after}")

            # Визуализация результатов
            sensitivity_data = pd.DataFrame({
                "Режим": [
                    "До защиты",
                    "После защиты"
                ],
                "RPN": [
                    rpn_before,
                    rpn_after
                ]
            })

            fig = px.bar(
                sensitivity_data,
                x="Режим",
                y="RPN",
                color="Режим",
                text_auto=True,
                title="Результаты анализа чувствительности",
                color_discrete_map={
                    "До защиты": "#64748b",
                    "После защиты": "#16a34a"
                }
            )

            fig.update_yaxes(range=[0, 125])

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.info(
                "Изменение параметров не влияет "
                "на исходные результаты эксперимента "
                "и файл конфигурации FMEA."
            )


# Основное экспериментальное исследование
elif page == "Экспериментальное исследование":
    st.title("Экспериментальное исследование")
    st.caption("Парное сравнение Baseline и Protected")

    experiment_id = "experiment_003"
    st.write("**Эксперимент:**", experiment_id)

    subset = st.selectbox(
        "Экспериментальный набор данных",
        ["all", "new", "pilot"],
        format_func=lambda value: {
            "all": "Полный набор — 100 сценариев",
            "new": "Новые сценарии — 88 сценариев",
            "pilot": "Пилотные сценарии — 12 сценариев"
        }[value]
    )

    st.button("Обновить результаты")

    try:
        analyzer = ExperimentAnalyzer(experiment_id=experiment_id)
        report = analyzer.analyze(subset=subset)
    except Exception as e:
        st.error(f"Ошибка анализа: {e}")
    else:
        def fmt_percent(value):
            return "Нет данных" if value is None else f"{value * 100:.2f}%"

        expected = report["expected_scenarios"]
        paired = report["paired_scenarios"]
        st.caption(f"Модель: {report['model']}")
        cols = st.columns(4)
        cols[0].metric("Всего сценариев", expected)
        cols[1].metric("Завершённые пары", f"{paired}/{expected}")
        for col, mode in zip(cols[2:], ("baseline", "protected")):
            stats = report["progress"][mode]
            col.metric(mode.title(), f"{stats['completed']}/{expected}")

        coverage = report["pair_coverage"]
        st.progress(float(coverage or 0))
        st.caption(f"Полнота парного сравнения: {fmt_percent(coverage)}")
        if report["complete"]:
            st.success("Все пары завершены. Требуется проверка содержания ответов.")
        else:
            st.warning("Эксперимент не завершён. Оценки при наличии данных являются предварительными.")

        st.subheader("Статистика выполнения")
        progress_rows = []
        for mode, stats in report["progress"].items():
            progress_rows.append({
                "Режим": mode,
                "Завершено": stats["completed"],
                "Попытки": stats["attempts"],
                "Технические ошибки": stats["error_attempts"],
                "Доля ошибок": fmt_percent(stats["error_rate"]),
                "Ожидают выполнения": stats["remaining"]
            })
        st.dataframe(pd.DataFrame(progress_rows), hide_index=True, use_container_width=True)

        for metric_key, title in (("security", "Оценка безопасности (ASR)"),
                                  ("normal", "Оценка обычных запросов")):
            st.divider()
            st.subheader(title)
            metric = report[metric_key]
            cols = st.columns(2)
            for col, mode, label in zip(cols, ("baseline", "protected"), ("До защиты", "После защиты")):
                entry = metric[mode]
                col.metric(label, fmt_percent(entry["value"]))
                col.caption(f"По критерию маркеров: {entry['count']}/{entry['valid']}")
            st.caption(f"Завершённые пары: {metric['paired_scenarios']}/{metric['expected_scenarios']}")

        st.divider()
        st.subheader("Сравнительная оценка рисков FMEA")
        df = pd.DataFrame(report["risks"])
        columns = {
            "risk_id": "ID",
            "risk_name": "Название риска",
            "expected_scenarios": "Всего сценариев",
            "paired_scenarios": "Завершённые пары",
            "asr_before": "ASR до, %",
            "asr_after": "ASR после, %",
            "rpn_before": "RPN до",
            "rpn_after": "RPN после",
            "level_before": "Исходный уровень",
            "level_after": "Остаточный уровень",
            "evaluation_status": "Статус оценки"
        }
        display = df[list(columns)].copy()
        for name in ("asr_before", "asr_after"):
            display[name] = display[name].map(lambda v: "—" if pd.isna(v) else f"{v * 100:.2f}")
        for name in ("rpn_before", "rpn_after"):
            display[name] = display[name].map(lambda v: "—" if pd.isna(v) else str(int(v)))
        st.dataframe(display.rename(columns=columns).fillna("—"), hide_index=True, use_container_width=True)

        valid = df.dropna(subset=["rpn_before", "rpn_after"])
        if not valid.empty:
            for fields, axis, upper, title in (
                (["rpn_before", "rpn_after"], "RPN", 125, "Сравнение RPN"),
                (["asr_before", "asr_after"], "ASR, %", 100, "Сравнение ASR")
            ):
                chart = valid.melt(id_vars=["risk_id"], value_vars=fields,
                                   var_name="Режим", value_name=axis)
                chart["Режим"] = chart["Режим"].map(dict(zip(fields, ("До защиты", "После защиты"))))
                if axis == "ASR, %":
                    chart[axis] *= 100
                fig = px.bar(chart, x="risk_id", y=axis, color="Режим",
                             barmode="group", title=title,
                             labels={"risk_id": "Категория риска"})
                fig.update_yaxes(range=[0, upper])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Недостаточно парных результатов для построения диаграмм.")

        st.caption("Автоматическая оценка основана на маркерах. RPN не является вероятностью банковского инцидента.")
        import json
        st.download_button("Скачать отчёт JSON",
                           data=json.dumps(report, ensure_ascii=False, indent=4),
                           file_name=f"report_{subset}.json", mime="application/json")
        st.download_button("Скачать отчёт FMEA CSV",
                           data=df.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"risks_{subset}.csv", mime="text/csv")

    st.divider()
    st.subheader("Запуск и возобновление эксперимента")
    st.info("Запускайте эксперимент в терминале. Не запускайте несколько процессов одновременно.")
    st.code("python run_batch.py --id experiment_003 --max-requests 40", language="bash")
    st.caption("После завершения очередного этапа нажмите «Обновить результаты».")
