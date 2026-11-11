from pathlib import Path

from src.extraction import extract_sales, extract_holidays
from src.cleaning import diagnose_quality, clean_sales
from src.transformation import transform_sales
from src.integration import integrate_sales_holidays
from src.validation import validate_integration

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"


def main():
    # PASO 1: EXTRACCIÓN
    sales = extract_sales()
    holidays_df = extract_holidays()

    # PASO 2: DIAGNÓSTICO Y LIMPIEZA
    diagnose_quality(sales)
    sales_clean = clean_sales(sales)

    # PASO 3: TRANSFORMACIÓN
    sales_transformed = transform_sales(sales_clean)

    # PASO 4: INTEGRACIÓN CON FESTIVOS
    sales_integrated = integrate_sales_holidays(sales_transformed, holidays_df)

    # PASO 5: VALIDACIÓN DE LA INTEGRACIÓN
    report = validate_integration(sales_transformed, holidays_df, sales_integrated)

    # PASO 6: GUARDAR LOS RESULTADOS
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    sales_transformed.to_csv(PROCESSED_DIR / "sales_transformed.csv", index=False)
    print(f"\nGuardado: data/processed/sales_transformed.csv ({len(sales_transformed)} filas)")

    sales_integrated.to_csv(PROCESSED_DIR / "sales_integrated.csv", index=False)
    print(f"Guardado: data/processed/sales_integrated.csv ({len(sales_integrated)} filas)")

    report.to_csv(OUTPUTS_DIR / "validacion_integracion.csv", index=False)
    print("Guardado: outputs/validacion_integracion.csv")


if __name__ == "__main__":
    main()
