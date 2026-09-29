"""
Descarga precios históricos y estados financieros de las armadoras
usando yfinance y los guarda en data/raw/.

Uso (desde la raíz del repo):
    python src/descarga_datos.py
"""
import pandas as pd
import yfinance as yf

from config import EMPRESAS, FECHA_INICIO, FECHA_FIN, DATA_RAW


def descargar_precios() -> pd.DataFrame:
    """Precio de cierre ajustado diario de todas las empresas."""
    tickers = list(EMPRESAS.values())
    datos = yf.download(tickers, start=FECHA_INICIO, end=FECHA_FIN,
                        auto_adjust=True, progress=False)["Close"]
    # Renombrar columnas de ticker a nombre de empresa
    datos = datos.rename(columns={v: k for k, v in EMPRESAS.items()})
    return datos[list(EMPRESAS.keys())]


def descargar_financieros() -> pd.DataFrame:
    """Ingresos, utilidades e I+D anuales (yfinance da ~4 años)."""
    campos = {
        "Total Revenue": "ingresos",
        "Operating Income": "utilidad_operativa",
        "Net Income": "utilidad_neta",
        "Research And Development": "id_gasto",
    }
    filas = []
    for nombre, ticker in EMPRESAS.items():
        try:
            t = yf.Ticker(ticker)
            estado = t.income_stmt
            moneda = t.fast_info.get("currency", "N/D")
        except Exception as e:
            print(f"  ⚠ No se pudo descargar {nombre}: {e}")
            continue
        for fecha in estado.columns:
            fila = {"empresa": nombre, "anio": fecha.year, "moneda": moneda}
            for original, nuevo in campos.items():
                fila[nuevo] = estado.loc[original, fecha] if original in estado.index else None
            filas.append(fila)
    return pd.DataFrame(filas).sort_values(["empresa", "anio"])


if __name__ == "__main__":
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    print("Descargando precios...")
    precios = descargar_precios()
    precios.to_csv(DATA_RAW / "precios.csv")
    print(f"  ✓ {precios.shape[0]} días x {precios.shape[1]} empresas")

    print("Descargando estados financieros...")
    fin = descargar_financieros()
    fin.to_csv(DATA_RAW / "financieros.csv", index=False)
    print(f"  ✓ {len(fin)} registros")
