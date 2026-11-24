import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_json(filename: str) -> dict:
    file_path = DATA_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_customers() -> list:
    return load_json("customers.json")["customers"]


def load_bank_info() -> dict:
    return load_json("bank_info.json")


def get_customer(customer_id: str):
    customers = load_customers()

    for customer in customers:
        if customer["customer_id"] == customer_id:
            return customer

    return None

def load_risk_catalog() -> list:
    """Загрузка каталога рисков информационной безопасности."""
    return load_json("risk_catalog.json")["risks"]

def load_test_cases() -> list:
    """Загрузка тестовых сценариев."""
    return load_json("test_cases.json")["test_cases"]

def load_fmea_config() -> dict:
    """Загрузка параметров модели FMEA."""
    return load_json("fmea_config.json")