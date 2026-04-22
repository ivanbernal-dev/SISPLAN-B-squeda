# Analítica BI — Replicación del Power BI oficial

Notebooks que reproducen, usando **solo pandas + numpy + matplotlib**, el
procesamiento que hace el sistema UBPD al alimentar el dashboard BI (Páginas 1
y 2 del archivo Power BI oficial).

El objetivo es poder **contrastar** que los datos que se ven en la plataforma
son los mismos del Excel original y los mismos que están en la base de datos.

## Estructura

```
analitica_bi/
├── README.md
├── requirements.txt
├── data/
│   └── Metas 2026_GITT_ Para power BI.xlsx   ← Excel fuente
├── src/
│   └── loaders.py                            ← helpers Excel↔DB
├── 01_pagina1_indicadores_y_ejecucion.ipynb  ← notebook Página 1
└── 02_pagina2_comparacion_grupos.ipynb       ← notebook Página 2
```

## Instalación

```bash
cd analitica_bi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook
```

## Fuentes de datos

Cada notebook carga los datos como un **diccionario** cuya llave es el nombre
de la hoja del Excel original (`PRB`, `EstructuraIndicadores`, `Historico`):

```python
from loaders import load_from_excel, load_from_db

data_excel = load_from_excel("data/Metas 2026_GITT_ Para power BI.xlsx")
data_db    = load_from_db("http://localhost/api", "admin", "Admin@UBPD2024!")
```

Ambas fuentes devuelven el mismo esquema. Para alternar, los notebooks tienen
una celda con:

```python
SOURCE = "excel"   # o "db"
data = data_excel if SOURCE == "excel" else data_db
```

## Endpoint backend (fuente DB)

Los notebooks consumen:

- `POST /api/auth/login` — para obtener el JWT
- `GET /api/admin/bi/raw` — retorna las 3 tablas tal como están en la BD, con
  los mismos nombres de columna del Excel original.
- `GET /api/bi/comparison` — para contrastar la comparación A vs B
  (solo usado en el notebook 2 como validación cruzada).

## Resultado esperado

Si el dataset en la base de datos es el mismo que está en el Excel:

- Los **KPIs globales** (meta total, avance, % global, PRBs únicos,
  indicadores únicos) deben coincidir al centavo.
- Las **13 tarjetas de indicadores** deben mostrar los mismos valores
  (Dato 2025 / Avance 2026 / Meta 2026 / %) que se ven en el BI.
- La **gráfica de ejecución mensual** (Ene=1.295, Feb=1.385, Mar–Dic=0) debe
  ser idéntica.
- La **línea de Dato 2025 = 10.276** coincide con la del BI.
- Las **barras espejadas** y los **labels analíticos** (Hallazgo, Resumen,
  Estados, Brecha) se calculan con las mismas fórmulas que usa el backend.

## Cambiar filtros

Los notebooks reproducen los filtros **por defecto** del BI (AÑO=2026,
Regional=Todas, GITT=Todas, PRB=Todos, Indicador=Todos). Hay una celda clara
donde puedes modificarlos:

```python
F_ANIO      = 2026
F_REGIONAL  = "CENTRO"    # o None
F_GITT      = None
F_PRB       = None
F_INDICADOR = None
```

## Notas

- Las filas del Excel con `AÑO` vacío (PRBs "Sin Determinar") se descartan,
  igual que lo hace el BI oficial.
- Los tipos numéricos (`Meta`, `Avance Total`, `Mes 1..12`, `Línea Base 2025`)
  se fuerzan con `pd.to_numeric(..., errors="coerce").fillna(0)`.
- El notebook 2 tiene una celda final de **contraste contra el backend** que
  llama a `GET /api/bi/comparison` y verifica que las diferencias sean 0.
