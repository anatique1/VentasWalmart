"""
cleaning.py
1) Diagnóstico de calidad (ANTES de limpiar) -> outputs/
2) Limpieza del dataset de ventas
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"

# Columnas de texto categórico donde buscamos variantes mal escritas
CATEGORICAL_COLS = [
    "Customer_Gender", "Order_Status", "Product_Category",
    "Payment_Method", "City", "Region",
]


# ----------------------------------------------------------------------
# 1. DIAGNÓSTICO
# ----------------------------------------------------------------------
def diagnose_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Revisa la calidad del dataset SIN modificarlo y guarda dos reportes."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # (a) Reporte por columna: tipo, nulos y valores únicos
    columns_report = pd.DataFrame({
        "Tipo": df.dtypes.astype(str),
        "Nulos": df.isna().sum(),
        "Pct_Nulos": (df.isna().mean() * 100).round(2),
        "Valores_Unicos": df.nunique(),
    })
    columns_report.index.name = "Columna"
    columns_report.to_csv(OUTPUT_DIR / "diagnostico_columnas.csv")

    # (b) Reporte de problemas concretos
    issues = [
        ("Filas duplicadas exactas", int(df.duplicated().sum())),
        ("Transaction_ID repetido", int(df["Transaction_ID"].duplicated().sum())),
        ("Quantity <= 0", int((df["Quantity"] <= 0).sum())),
        ("Customer_Age fuera de 18-90", int(((df["Customer_Age"] < 18) | (df["Customer_Age"] > 90)).sum())),
        ("Discount_Percentage > 100", int((df["Discount_Percentage"] > 100).sum())),
        ("Profit != Sales - Cost", int(((df["Sales_Amount"] - df["Cost_Amount"] - df["Profit"]).abs() > 0.02).sum())),
    ]
    # Variantes de escritura: valores distintos vs. valores distintos "normalizados"
    for col in CATEGORICAL_COLS:
        raw = df[col].dropna().nunique()
        norm = df[col].dropna().str.strip().str.lower().str.replace(r"[\s\-]", "", regex=True).nunique()
        issues.append((f"Variantes de escritura en {col}", raw - norm))

    issues_report = pd.DataFrame(issues, columns=["Problema", "Cantidad"])
    issues_report.to_csv(OUTPUT_DIR / "diagnostico_problemas.csv", index=False)

    print("\n[cleaning] ===== DIAGNÓSTICO DE CALIDAD =====")
    print(issues_report.to_string(index=False))
    print("\nColumnas con nulos:")
    print(columns_report[columns_report["Nulos"] > 0][["Nulos", "Pct_Nulos"]])
    return issues_report


# ----------------------------------------------------------------------
# 2. LIMPIEZA
# ----------------------------------------------------------------------
def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia limpia del dataset. Cada paso queda en un log."""
    df = df.copy()
    log = []
    rows_start = len(df)

    # --- 1. Duplicados -------------------------------------------------
    # Una misma transacción repetida infla ventas y ganancias.
    n = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    log.append(f"Duplicados exactos eliminados: {n}")

    # --- 2. Espacios sobrantes en texto -------------------------------
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        df[col] = df[col].str.strip()
    log.append("Espacios al inicio/final eliminados en columnas de texto")

    # --- 3. Estandarizar categorías ------------------------------------
    # 'paypal' y 'PayPal' son lo mismo, pero Python las cuenta como distintas.
    payment_map = {
        "creditcard": "Credit Card", "debitcard": "Debit Card",
        "paypal": "PayPal", "applepay": "Apple Pay",
        "cash": "Cash", "banktransfer": "Bank Transfer",
    }
    key = df["Payment_Method"].str.lower().str.replace(r"\s", "", regex=True)
    df["Payment_Method"] = key.map(payment_map)

    gender_map = {"male": "Male", "female": "Female",
                  "nonbinary": "Non-binary"}
    key = df["Customer_Gender"].str.lower().str.replace(r"[\s\-]", "", regex=True)
    df["Customer_Gender"] = key.map(gender_map)

    df["Order_Status"] = df["Order_Status"].str.capitalize()

    category_map = {"electronics": "Electronics", "furniture": "Furniture",
                    "appliances": "Appliances", "office supplies": "Office Supplies"}
    df["Product_Category"] = df["Product_Category"].str.lower().map(category_map)

    df["City"] = df["City"].str.title()
    df["Region"] = df["Region"].replace({
        "NRW": "North Rhine-Westphalia",
        "British columbia": "British Columbia",
        "North East": "Northeast",   # en EE.UU. (no en Reino Unido)
    })
    log.append("Categorías estandarizadas: pago, género, estado, categoría, ciudad y región")

    # --- 4. Valores imposibles -> se tratan como nulos ----------------
    # Edades <18 o >90 y descuentos >100% son errores de captura.
    bad_age = (df["Customer_Age"] < 18) | (df["Customer_Age"] > 90)
    df.loc[bad_age, "Customer_Age"] = pd.NA
    bad_disc = df["Discount_Percentage"] > 100
    df.loc[bad_disc, "Discount_Percentage"] = pd.NA
    log.append(f"Edades inválidas pasadas a nulo: {int(bad_age.sum())}; descuentos >100%: {int(bad_disc.sum())}")

    # Cantidad <= 0 no es una venta válida: se eliminan esas filas.
    bad_qty = df["Quantity"] <= 0
    log.append(f"Filas con Quantity <= 0 eliminadas: {int(bad_qty.sum())}")
    df = df[~bad_qty].reset_index(drop=True)

    # --- 5. Valores nulos ----------------------------------------------
    # 5a. Recuperar el dato desde otra columna que lo identifica de forma única.
    name_by_customer = df.groupby("Customer_ID")["Customer_Name"].first()
    df["Customer_Name"] = df["Customer_Name"].fillna(df["Customer_ID"].map(name_by_customer))

    name_by_product = df.groupby("Product_ID")["Product_Name"].first()
    df["Product_Name"] = df["Product_Name"].fillna(df["Product_ID"].map(name_by_product))

    # 5b. Imputar con la mediana (resistente a valores extremos).
    df["Customer_Age"] = df["Customer_Age"].fillna(df["Customer_Age"].median()).round()
    df["Discount_Percentage"] = df["Discount_Percentage"].fillna(df["Discount_Percentage"].median())
    # Los días de entrega dependen del método de envío (Next Day vs Standard).
    df["Delivery_Days"] = df["Delivery_Days"].fillna(
        df.groupby("Shipping_Method")["Delivery_Days"].transform("median"))
    df["Inventory_Level"] = df["Inventory_Level"].fillna(
        df.groupby("Product_ID")["Inventory_Level"].transform("median"))

    # 5c. Categorías sin dato -> etiqueta explícita.
    for col in ["Customer_Name", "Customer_Gender", "Payment_Method"]:
        df[col] = df[col].fillna("Unknown")
    # Nulo esperado: sin promoción / sin devolución no es un error.
    df["Promotion_Code"] = df["Promotion_Code"].fillna("No Promo")
    df["Return_Reason"] = df["Return_Reason"].fillna("No Return")

    # Customer_Rating se deja nulo a propósito: inventar la opinión de un
    # cliente sesgaría el análisis.
    log.append("Nulos tratados: recuperados por ID, mediana, etiqueta 'Unknown'/'No Promo'/'No Return'. "
               "Customer_Rating se deja sin imputar")

    # --- 6. Coherencia numérica ----------------------------------------
    n = int(((df["Sales_Amount"] - df["Cost_Amount"] - df["Profit"]).abs() > 0.02).sum())
    df["Profit"] = (df["Sales_Amount"] - df["Cost_Amount"]).round(2)
    log.append(f"Profit recalculado como Sales - Cost ({n} filas no coincidían)")

    log.append(f"Filas: {rows_start} -> {len(df)}")

    # Guardar el log y mostrarlo
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "log_limpieza.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n[cleaning] ===== LIMPIEZA =====")
    for line in log:
        print(" -", line)
    return df