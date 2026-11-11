"""
integration.py
Integra las ventas transformadas con la tabla de festivos.
Resultado: cada venta queda marcada con Is_Holiday (True/False)
y el nombre del festivo, si lo hay.

Llave de unión: (Country, fecha)  -> relación muchos-a-uno (m:1)
Tipo de unión:  LEFT JOIN (se conservan todas las ventas)
"""

import pandas as pd


def prepare_holidays(holidays_df: pd.DataFrame) -> pd.DataFrame:
    """I1. Dejar la tabla de festivos lista para unir.
    Por qué: la fecha debe ser del mismo tipo que Order_Date, y la llave
    (Country, Holiday_Date) debe ser única. Si un país tuviera dos festivos
    el mismo día, el join duplicaría esas ventas; por eso se consolidan
    los nombres en una sola fila."""
    df = holidays_df.copy()
    df["Country"] = df["Country"].str.strip()
    df["Holiday_Date"] = pd.to_datetime(df["Holiday_Date"], format="%Y-%m-%d")
    df = (
        df.groupby(["Country", "Holiday_Date"], as_index=False)
        .agg(Holiday_Name=("Holiday_Name", lambda x: " | ".join(sorted(set(x)))))
    )
    return df


def add_holiday_flag(sales: pd.DataFrame, holidays_dim: pd.DataFrame) -> pd.DataFrame:
    """I2. Unir ventas con festivos y crear Is_Holiday.
    Por qué: se une por país Y fecha, porque un mismo día puede ser festivo
    en un país y no en otro. validate='many_to_one' hace que pandas lance
    un error si la relación no es m:1 (evita la multiplicación de filas)."""
    df = sales.copy()
    df["Country"] = df["Country"].str.strip()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])

    merged = df.merge(
        holidays_dim,
        how="left",
        left_on=["Country", "Order_Date"],
        right_on=["Country", "Holiday_Date"],
        validate="many_to_one",
        indicator=True,
    )
    merged["Is_Holiday"] = merged["_merge"].eq("both")
    merged["Holiday_Name"] = merged["Holiday_Name"].fillna("No Holiday")
    return merged.drop(columns=["Holiday_Date", "_merge"])


def integrate_sales_holidays(sales: pd.DataFrame, holidays_df: pd.DataFrame) -> pd.DataFrame:
    """Aplica la integración completa."""
    holidays_dim = prepare_holidays(holidays_df)
    integrated = add_holiday_flag(sales, holidays_dim)

    n_fest = int(integrated["Is_Holiday"].sum())
    print("\n[integration] ===== INTEGRACIÓN VENTAS + FESTIVOS =====")
    print(f" - Festivos únicos (país, fecha): {len(holidays_dim)}")
    print(f" - Ventas en festivo: {n_fest} de {len(integrated)} ({n_fest / len(integrated):.2%})")
    print(" - Columnas nuevas: ['Holiday_Name', 'Is_Holiday']")
    return integrated
