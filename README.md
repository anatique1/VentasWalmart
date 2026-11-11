# VentasWalmart: transformación e integración de datos para la analítica

Pipeline en Python que toma un dataset de transacciones de venta, lo limpia y lo transforma, y después lo cruza con un calendario de festivos. Así se puede saber si cada venta ocurrió en un día festivo del país donde se hizo.

El resultado final es `data/processed/sales_integrated.csv`: **17.992 transacciones** (2022–2025, 6 países) con variables de fecha, de cliente y de rentabilidad, y con la marca `Is_Holiday`.

---

## Estructura del proyecto

```
VentasWalmart/
├── main.py                     # Orquesta todo el pipeline (pasos 1 a 6)
├── requirements.txt            # Dependencias: pandas, holidays
├── src/
│   ├── extraction.py           # Paso 1: lee las ventas y genera los festivos
│   ├── cleaning.py             # Paso 2: diagnóstico de calidad y limpieza
│   ├── transformation.py       # Paso 3: nuevas variables (fecha, edad, descuento, margen…)
│   ├── integration.py          # Paso 4: cruce ventas + festivos (Is_Holiday)
│   └── validation.py           # Paso 5: validaciones de la integración
├── data/
│   ├── raw/
│   │   ├── Sales_transactions.csv   # Fuente original de ventas (no se modifica)
│   │   └── holidays_raw.csv         # Festivos generados con la librería `holidays`
│   └── processed/
│       ├── sales_clean.csv          # Versión intermedia limpia (main.py no la regenera)
│       ├── sales_transformed.csv    # Ventas limpias + transformaciones
│       └── sales_integrated.csv     # RESULTADO FINAL: ventas + festivos
├── outputs/
│   ├── diagnostico_columnas.csv     # Tipo, nulos y valores únicos por columna (antes de limpiar)
│   ├── diagnostico_problemas.csv    # Problemas de calidad encontrados
│   ├── log_limpieza.txt             # Resumen de lo que hizo la limpieza
│   └── validacion_integracion.csv   # Resultado de las 11 validaciones
├── notebooks/
│   └── dataset_fehas.ipynb          # Exploración inicial de la librería `holidays`
└── docs/
    └── informe.pdf                  # Informe del proyecto
```

---

## Cómo reproducirlo

### Requisitos
- **Python 3.10 o superior** ([python.org](https://www.python.org/downloads/))
- **Git** ([git-scm.com](https://git-scm.com))

### 1. Clonar el repositorio
```bash
git clone https://github.com/anatique1/VentasWalmart.git
cd VentasWalmart
```

### 2. Crear y activar un entorno virtual
**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```
> Si PowerShell bloquea la activación ("ejecución de scripts deshabilitada"), ejecuta una vez
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a activar.

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el pipeline
```bash
python main.py
```

Ejecútalo desde la **raíz del repositorio**, es decir, la carpeta donde está `main.py`.

### 5. Verificar el resultado
Al final de la consola deberías ver:
```
[validation] ===== VALIDACIONES DE LA INTEGRACIÓN =====
 [OK] Transaction_ID único en ventas -> 0 duplicados
 ...
 - 11 de 11 validaciones aprobadas

Guardado: data/processed/sales_transformed.csv (17992 filas)
Guardado: data/processed/sales_integrated.csv (17992 filas)
Guardado: outputs/validacion_integracion.csv
```
Si alguna validación falla, el programa se detiene con un `ValueError` que indica cuál falló.

---

## Qué hace cada paso

### Paso 1. Extracción (`src/extraction.py`)
- Lee `data/raw/Sales_transactions.csv` sin modificarlo: 18.045 filas y 36 columnas.
- Genera los festivos nacionales de **Estados Unidos, Reino Unido, Canadá, Alemania, Francia y Australia** para **2022–2025** con la librería [`holidays`](https://pypi.org/project/holidays/) y los guarda en `data/raw/holidays_raw.csv` (210 festivos).

### Paso 2. Diagnóstico y limpieza (`src/cleaning.py`)
Primero **diagnostica sin modificar nada** y guarda los reportes en `outputs/`. Después limpia:

| Problema | Tratamiento |
|---|---|
| 45 filas duplicadas exactas | Eliminadas |
| Espacios al inicio o final en texto | Eliminados |
| Variantes de escritura (género, estado, categoría, pago, ciudad, región) | Estandarizadas |
| 4 edades fuera de 18–90 y 1 descuento > 100 % | Pasadas a nulo |
| 8 filas con `Quantity <= 0` | Eliminadas |
| Nulos | Recuperados por ID, mediana o etiquetas `Unknown` / `No Promo` / `No Return`. `Customer_Rating` se deja sin imputar |
| 110 filas con `Profit != Sales - Cost` | `Profit` recalculado |

Resultado: **18.045 → 17.992 filas**.

### Paso 3. Transformación (`src/transformation.py`)
| Columna nueva | Descripción |
|---|---|
| `Order_Month`, `Order_Quarter`, `Order_Weekday` | Componentes de la fecha para analizar estacionalidad |
| `Is_Weekend` | 1 si la compra fue sábado o domingo |
| `Age_Group` | Rangos de edad: 18-25, 26-35, 36-45, 46-55, 56+ |
| `Discount_Level` | No Discount / Low (1-10%) / High (>10%) |
| `Profit_Margin_Pct` | Margen = Profit / Sales_Amount × 100 |
| `Is_Returned` | `Return_Flag` codificado como 1/0 |

### Paso 4. Integración con festivos (`src/integration.py`)
- **Llave de unión:** `(Country, Order_Date)` ↔ `(Country, Holiday_Date)`. Se usa el país además de la fecha porque un mismo día puede ser festivo en un país y no en otro. Ninguna de las dos fuentes trae un ID de festivo, así que se usa esta llave compuesta natural, que es única por festivo.
- **Tipo de unión:** `LEFT JOIN` **muchos a uno** (`validate="many_to_one"`), así que se conservan todas las ventas. Si la tabla de festivos tuviera la llave repetida, pandas lanza un error en lugar de duplicar filas.
- Si un país tuviera dos festivos el mismo día, sus nombres se consolidan en una sola fila (`"A | B"`) antes del join.

| Columna nueva | Descripción |
|---|---|
| `Is_Holiday` | `True` si la venta fue en un festivo del país, `False` si no |
| `Holiday_Name` | Nombre del festivo, o `No Holiday` |

### Paso 5. Validación (`src/validation.py`)
| # | Validación | Qué evita |
|---|---|---|
| V1 | `Transaction_ID` único en ventas | Grano de la tabla mal definido |
| V2 | Llave `(Country, Holiday_Date)` única | Multiplicación de filas en el join |
| V3 | Todos los países de ventas tienen calendario | Festivos no detectados por falta de datos |
| V4 | Todos los años de ventas tienen calendario | Ídem |
| V5 | Mismo número de filas antes y después | Pérdida o duplicación de filas |
| V6 | `Transaction_ID` sigue siendo único | Explosión por cardinalidad |
| V7 | Mismo conjunto de transacciones | Filas perdidas o inventadas |
| V8 | Totales de `Sales_Amount` y `Profit` iguales | Distorsión de métricas |
| V9 | `Is_Holiday` booleana, sin nulos y coherente con `Holiday_Name` | Flag mal construido |
| V10 | Recalcular el flag sin merge y comparar | Errores en la lógica del join |
| V11 | Columnas originales sin cambios | Modificaciones accidentales |

### Paso 6. Guardado
Escribe `sales_transformed.csv`, `sales_integrated.csv` y `outputs/validacion_integracion.csv`.

---

## Resultados principales

- **17.992** transacciones finales, sin pérdida ni duplicación en la integración.
- **Ventas totales:** 8.229.473,04 · **Ganancia total:** 1.643.056,73
- **498 ventas (2,77 %)** ocurrieron en un día festivo; 169 de los 210 festivos tuvieron ventas.

| País | Ventas en festivo | Total ventas | % |
|---|---:|---:|---:|
| Australia | 21 | 1.113 | 1,89 % |
| Canadá | 41 | 2.678 | 1,53 % |
| Francia | 56 | 1.578 | 3,55 % |
| Alemania | 69 | 2.125 | 3,25 % |
| Reino Unido | 74 | 2.972 | 2,49 % |
| Estados Unidos | 237 | 7.526 | 3,15 % |

Los festivos con más transacciones fueron **Christmas Day** (68), **Good Friday** (34) y **Thanksgiving Day** (33).

---

## Notas

- `data/raw/holidays_raw.csv` **se regenera en cada ejecución** a partir de la librería `holidays`. Si una versión nueva de la librería cambia algún festivo, los resultados podrían variar levemente.
- Los festivos son **nacionales**. No se incluyen festivos regionales o estatales (por ejemplo, de un estado de EE. UU. o de un *Land* alemán).
- Los festivos "observed" son los que se trasladan cuando caen en fin de semana, y se tratan como festivos.