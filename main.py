from pathlib import Path

from src.extraction import extract_sales, extract_holidays
from src.cleaning import diagnose_quality, clean_sales

# Carpeta donde se guardan los datos ya limpios
PROCESSED_DIR = Path(__file__).resolve().parent / "data" / "processed"


def main():
    # PASO 1: EXTRACCIÓN
    # Lee el CSV de ventas y genera los festivos con la librería
    sales = extract_sales()
    holidays_df = extract_holidays()

    # PASO 2: DIAGNÓSTICO Y LIMPIEZA
    # Primero revisa qué está mal (guarda informes en outputs/)
    diagnose_quality(sales)
    # Después arregla los problemas
    sales_clean = clean_sales(sales)

    # PASO 3: GUARDAR EL RESULTADO
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sales_clean.to_csv(PROCESSED_DIR / "sales_clean.csv", index=False)
    print(f"\nGuardado: data/processed/sales_clean.csv ({len(sales_clean)} filas)")


if __name__ == "__main__":
    main()