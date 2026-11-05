"""
transformation.py
Transformaciones sobre el dataset de ventas YA limpio.
Cada función hace UNA transformación y explica por qué.
"""

import pandas as pd


def convert_order_date(df: pd.DataFrame) -> pd.DataFrame:
    """T1. Convertir Order_Date de texto a fecha real.
    Por qué: con texto no se puede sacar mes ni día de la semana, y para
    unir con la tabla de festivos las dos fechas deben ser del mismo tipo."""
    df = df.copy()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], format="%Y-%m-%d")
    return df


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    """T2. Crear mes, trimestre, día de la semana y fin de semana.
    Por qué: permiten analizar estacionalidad (¿se vende más en diciembre?
    ¿más en fin de semana?), algo imposible con una sola fecha."""
    df = df.copy()
    df["Order_Month"] = df["Order_Date"].dt.month
    df["Order_Quarter"] = df["Order_Date"].dt.quarter
    df["Order_Weekday"] = df["Order_Date"].dt.day_name()
    df["Is_Weekend"] = (df["Order_Date"].dt.dayofweek >= 5).astype(int)
    return df


def add_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """T3. Agrupar la edad en rangos.
    Por qué: 60 edades distintas son difíciles de analizar; en 5 rangos
    se comparan grupos de clientes con claridad."""
    df = df.copy()
    df["Age_Group"] = pd.cut(
        df["Customer_Age"],
        bins=[17, 25, 35, 45, 55, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "56+"],
    ).astype(str)
    return df


def add_discount_level(df: pd.DataFrame) -> pd.DataFrame:
    """T4. Clasificar el descuento en Sin descuento / Bajo / Alto.
    Por qué: el 42 % de las ventas no tiene descuento y el resto se concentra
    en pocos valores; una categoría es más fácil de comparar que un número."""
    df = df.copy()
    df["Discount_Level"] = pd.cut(
        df["Discount_Percentage"],
        bins=[-1, 0, 10, 100],
        labels=["No Discount", "Low (1-10%)", "High (>10%)"],
    ).astype(str)
    return df


def add_profit_margin(df: pd.DataFrame) -> pd.DataFrame:
    """T5. Calcular el margen de ganancia en porcentaje.
    Por qué: la ganancia en dinero no permite comparar un producto de $20
    con uno de $1.400; el margen (Profit / Ventas) sí."""
    df = df.copy()
    df["Profit_Margin_Pct"] = (df["Profit"] / df["Sales_Amount"] * 100).round(2)
    return df


def encode_return_flag(df: pd.DataFrame) -> pd.DataFrame:
    """T6. Convertir Return_Flag de Yes/No a 1/0.
    Por qué: con 1/0 se puede sumar y promediar directamente
    (el promedio es la tasa de devolución)."""
    df = df.copy()
    df["Is_Returned"] = (df["Return_Flag"] == "Yes").astype(int)
    return df


def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las transformaciones en orden."""
    steps = [
        convert_order_date,
        add_date_features,
        add_age_group,
        add_discount_level,
        add_profit_margin,
        encode_return_flag,
    ]
    cols_before = set(df.columns)
    for step in steps:
        df = step(df)

    new_cols = sorted(set(df.columns) - cols_before)
    print("\n[transformation] ===== TRANSFORMACIONES =====")
    print(f" - {len(steps)} transformaciones aplicadas")
    print(f" - Columnas nuevas: {new_cols}")
    return df