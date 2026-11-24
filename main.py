from src.bank_assistant import BankAssistant


def main():

    assistant = BankAssistant(mode="protected")

    print("Режим работы:", assistant.mode)

    # Имитация авторизованного сеанса клиента
    customer_id = "C001"

    print("Добро пожаловать в DemoBank")
    print("Модель:", assistant.llm.model)
    print("ID клиента:", customer_id)
    print("Для выхода введите 'exit'")

    while True:

        question = input("\nКлиент: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        try:
            response = assistant.ask(
                question=question,
                customer_id=customer_id
            )

            print("Ассистент:", response)
            print("Метаданные:", assistant.llm.last_metadata)

        except Exception as e:
            print("Ошибка:", e)
            print("Метаданные:", assistant.llm.last_metadata)


if __name__ == "__main__":
    main()