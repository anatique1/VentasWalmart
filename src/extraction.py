"""
extraction.py
Extrae las dos fuentes de datos del proyecto:
  1. CSV de ventas (archivo plano)  -> data/raw/Sales_transactions.csv
  2. Festivos generados con la librería `holidays` -> data/raw/holidays_raw.csv
"""

from pathlib import Path

import holidays
import pandas as pd

# Carpeta raíz del proyecto (dos niveles arriba de este archivo)
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

SALES_FILE = RAW_DIR / "Sales_transactions.csv"
HOLIDAYS_FILE = RAW_DIR / "holidays_raw.csv"

# Países del CSV -> código que usa la librería holidays
COUNTRY_CODES = {
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
    "Germany": "DE",
    "France": "FR",
    "Australia": "AU",
}

YEARS = range(2022, 2026)  # 2022 a 2025


def extract_sales() -> pd.DataFrame:
    """Lee el CSV de ventas tal como viene, sin modificarlo."""
    if not SALES_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {SALES_FILE}")
    df = pd.read_csv(SALES_FILE)
    print(f"[extraction] Ventas: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


def extract_holidays() -> pd.DataFrame:
    """Genera los festivos de cada país con la librería `holidays`
    y los guarda en data/raw/holidays_raw.csv."""
    records = []
    for country, code in COUNTRY_CODES.items():
        country_holidays = holidays.country_holidays(code, years=YEARS)
        for date, name in country_holidays.items():
            records.append(
                {"Country": country, "Holiday_Date": date, "Holiday_Name": name}
            )

    df = pd.DataFrame(records).sort_values(["Country", "Holiday_Date"])
    df.to_csv(HOLIDAYS_FILE, index=False)
    print(f"[extraction] Festivos: {df.shape[0]} filas guardadas en {HOLIDAYS_FILE.name}")
    return df