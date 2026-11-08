"""
validation.py
Validaciones de la integración ventas + festivos.
Cada función revisa UNA regla y devuelve (nombre, ok, detalle).
validate_integration() las ejecuta todas y lanza un error si alguna falla.
"""

import pandas as pd

from src.integration import prepare_holidays


# ---------------------------------------------------------------------------
# Validaciones PREVIAS al join
# ---------------------------------------------------------------------------
def check_sales_key_unique(sales: pd.DataFrame):
    """V1. Transaction_ID único en ventas (es el grano de la tabla)."""
    dups = int(sales["Transaction_ID"].duplicated().sum())
    return "Transaction_ID único en ventas", dups == 0, f"{dups} duplicados"


def check_holiday_key_unique(holidays_dim: pd.DataFrame):
    """V2. Llave (Country, Holiday_Date) única: si no, el join multiplica filas."""
    dups = int(holidays_dim.duplicated(["Country", "Holiday_Date"]).sum())
    return "Llave de festivos única", dups == 0, f"{dups} duplicados"


def check_country_coverage(sales: pd.DataFrame, holidays_dim: pd.DataFrame):
    """V3. Todo país de ventas tiene calendario de festivos."""
    missing = set(sales["Country"].str.strip()) - set(holidays_dim["Country"])
    return "Cobertura de países", not missing, f"sin calendario: {missing or 'ninguno'}"


def check_year_coverage(sales: pd.DataFrame, holidays_dim: pd.DataFrame):
    """V4. Todo año de ventas está cubierto por el calendario."""
    years_sales = set(pd.to_datetime(sales["Order_Date"]).dt.year)
    missing = years_sales - set(holidays_dim["Holiday_Date"].dt.year)
    return "Cobertura de años", not missing, f"sin calendario: {missing or 'ninguno'}"


# ---------------------------------------------------------------------------
# Validaciones POSTERIORES al join
# ---------------------------------------------------------------------------
def check_row_count(before: pd.DataFrame, after: pd.DataFrame):
    """V5. El join no agrega ni quita filas."""
    return ("Conservación de filas", len(before) == len(after),
            f"antes {len(before)} | después {len(after)}")


def check_no_row_explosion(after: pd.DataFrame):
    """V6. Cada transacción aparece una sola vez (sin multiplicación por cardinalidad)."""
    dups = int(after["Transaction_ID"].duplicated().sum())
    return "Sin multiplicación de filas", dups == 0, f"{dups} transacciones repetidas"


def check_same_transactions(before: pd.DataFrame, after: pd.DataFrame):
    """V7. Mismo conjunto de transacciones (no se pierde ni se inventa ninguna)."""
    same = set(before["Transaction_ID"]) == set(after["Transaction_ID"])
    return "Mismo conjunto de Transaction_ID", same, ""


def check_metrics_preserved(before: pd.DataFrame, after: pd.DataFrame):
    """V8. Los totales de ventas y ganancia no cambian."""
    s0, s1 = before["Sales_Amount"].sum(), after["Sales_Amount"].sum()
    p0, p1 = before["Profit"].sum(), after["Profit"].sum()
    ok = abs(s0 - s1) < 1e-6 and abs(p0 - p1) < 1e-6
    return "Totales conservados", ok, f"Sales {s1:,.2f} | Profit {p1:,.2f}"


def check_flag_quality(after: pd.DataFrame):
    """V9. Is_Holiday booleana, sin nulos y coherente con Holiday_Name."""
    ok = (
        after["Is_Holiday"].dtype == bool
        and after["Is_Holiday"].notna().all()
        and (after["Is_Holiday"] == after["Holiday_Name"].ne("No Holiday")).all()
    )
    return "Is_Holiday booleana y coherente", bool(ok), ""


def check_cross_validation(after: pd.DataFrame, holidays_dim: pd.DataFrame):
    """V10. Recalcular el flag con un método independiente (sin merge)."""
    keys = set(zip(holidays_dim["Country"], holidays_dim["Holiday_Date"]))
    expected = [(c, d) in keys for c, d in
                zip(after["Country"], pd.to_datetime(after["Order_Date"]))]
    ok = (after["Is_Holiday"].values == pd.Series(expected).values).all()
    return "Verificación cruzada del flag", bool(ok), ""


def check_original_columns(before: pd.DataFrame, after: pd.DataFrame):
    """V11. Las columnas originales no se modificaron."""
    cols = [c for c in before.columns if c not in ("Order_Date", "Country")]
    ok = after[cols].reset_index(drop=True).equals(before[cols].reset_index(drop=True))
    return "Columnas originales intactas", ok, ""


def validate_integration(sales: pd.DataFrame, holidays_df: pd.DataFrame,
                         integrated: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta todas las validaciones, imprime el reporte y devuelve
    un DataFrame con los resultados. Lanza error si alguna falla."""
    holidays_dim = prepare_holidays(holidays_df)
    results = [
        check_sales_key_unique(sales),
        check_holiday_key_unique(holidays_dim),
        check_country_coverage(sales, holidays_dim),
        check_year_coverage(sales, holidays_dim),
        check_row_count(sales, integrated),
        check_no_row_explosion(integrated),
        check_same_transactions(sales, integrated),
        check_metrics_preserved(sales, integrated),
        check_flag_quality(integrated),
        check_cross_validation(integrated, holidays_dim),
        check_original_columns(sales, integrated),
    ]

    print("\n[validation] ===== VALIDACIONES DE LA INTEGRACIÓN =====")
    for name, ok, detail in results:
        print(f" [{'OK' if ok else 'FALLA'}] {name}" + (f" -> {detail}" if detail else ""))

    report = pd.DataFrame(results, columns=["validacion", "ok", "detalle"])
    failed = report.loc[~report["ok"], "validacion"].tolist()
    if failed:
        raise ValueError(f"Validaciones fallidas: {failed}")
    print(f" - {len(results)} de {len(results)} validaciones aprobadas")
    return report
