from pathlib import Path

from src.extraction import extract_sales, extract_holidays
from src.cleaning import diagnose_quality, clean_sales
from src.transformation import transform_sales

PROCESSED_DIR = Path(__file__).resolve().parent / "data" / "processed"


def main():
    # PASO 1: EXTRACCIÓN
    sales = extract_sales()
    holidays_df = extract_holidays()

    # PASO 2: DIAGNÓSTICO Y LIMPIEZA
    diagnose_quality(sales)
    sales_clean = clean_sales(sales)

    # PASO 3: TRANSFORMACIÓN
    sales_transformed = transform_sales(sales_clean)

    # PASO 4: GUARDAR EL RESULTADO
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sales_transformed.to_csv(PROCESSED_DIR / "sales_transformed.csv", index=False)
    print(f"\nGuardado: data/processed/sales_transformed.csv ({len(sales_transformed)} filas)")


if __name__ == "__main__":
    main()