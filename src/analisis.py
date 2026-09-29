"""Funciones de análisis y gráficas que usa el notebook."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import CRISIS_CHIPS, IMAGES

sns.set_theme(style="whitegrid")
DIAS_BURSATILES = 252


def limpiar_precios(precios: pd.DataFrame) -> pd.DataFrame:
    """Las bolsas cierran en días distintos: rellenamos huecos con el último precio."""
    return precios.sort_index().ffill().dropna(how="all")


def normalizar(precios: pd.DataFrame, base: float = 100) -> pd.DataFrame:
    """Lleva todas las series a base 100 desde su primer dato válido.
    Así comparamos rendimiento aunque coticen en monedas distintas."""
    return precios.apply(lambda s: s / s.dropna().iloc[0] * base)


def metricas_riesgo_rendimiento(precios: pd.DataFrame) -> pd.DataFrame:
    """Rendimiento anualizado, volatilidad y máxima caída de cada empresa."""
    rend = precios.pct_change(fill_method=None)
    filas = {}
    for emp in precios.columns:
        s = precios[emp].dropna()
        anios = (s.index[-1] - s.index[0]).days / 365.25
        filas[emp] = {
            "rend_anual_%": ((s.iloc[-1] / s.iloc[0]) ** (1 / anios) - 1) * 100,
            "volatilidad_%": rend[emp].std() * np.sqrt(DIAS_BURSATILES) * 100,
            "max_caida_%": ((s / s.cummax()) - 1).min() * 100,
        }
    tabla = pd.DataFrame(filas).T
    tabla["rend/riesgo"] = tabla["rend_anual_%"] / tabla["volatilidad_%"]
    return tabla.round(2).sort_values("rend/riesgo", ascending=False)


def impacto_crisis_chips(precios: pd.DataFrame) -> pd.DataFrame:
    """Cuánto cayó cada empresa durante la crisis y cuánto tardó en recuperarse."""
    inicio, fin = CRISIS_CHIPS
    tramo = precios.loc[inicio:fin]
    resultados = {}
    for emp in precios.columns:
        s = tramo[emp].dropna()
        pico_fecha, pico = s.idxmax(), s.max()
        despues = s.loc[pico_fecha:]
        valle_fecha = despues.idxmin()
        caida = (despues.min() / pico - 1) * 100
        # ¿Cuándo volvió a superar el pico? Buscamos en toda la serie posterior
        post = precios[emp].loc[valle_fecha:]
        post = post[post >= pico]
        dias = (post.index[0] - valle_fecha).days if len(post) else "Aún no"
        resultados[emp] = {
            "caida_%": round(caida, 1),
            "fecha_pico": pico_fecha.date(),
            "fecha_valle": valle_fecha.date(),
            "dias_para_recuperar": dias,
        }
    return pd.DataFrame(resultados).T.sort_values("caida_%")


def margenes(fin: pd.DataFrame) -> pd.DataFrame:
    """Margen operativo, margen neto e intensidad de I+D (% de ingresos).
    Son porcentajes, así que no importa la moneda de cada empresa."""
    df = fin.copy()
    df["margen_operativo_%"] = df["utilidad_operativa"] / df["ingresos"] * 100
    df["margen_neto_%"] = df["utilidad_neta"] / df["ingresos"] * 100
    df["id_sobre_ingresos_%"] = df["id_gasto"] / df["ingresos"] * 100
    return df


# ---------------- Gráficas ----------------

def _guardar(fig, nombre):
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES / nombre, dpi=150, bbox_inches="tight")


def graficar_normalizado(norm: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 6))
    norm.plot(ax=ax, linewidth=1.5)
    ax.axvspan(*pd.to_datetime(CRISIS_CHIPS), color="red", alpha=0.08)
    ax.text(pd.Timestamp(CRISIS_CHIPS[0]), ax.get_ylim()[1], " Crisis de chips",
            va="top", fontsize=9, color="darkred")
    ax.set_yscale("log")
    ax.set_title("Evolución de $100 invertidos (escala log)")
    ax.set_ylabel("Valor (base 100)")
    ax.set_xlabel("")
    ax.legend(ncol=4, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.06), frameon=False)
    _guardar(fig, "01_precio_normalizado.png")
    return fig


def graficar_riesgo_rendimiento(tabla: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(tabla["volatilidad_%"], tabla["rend_anual_%"], s=120)
    for emp, fila in tabla.iterrows():
        ax.annotate(emp, (fila["volatilidad_%"], fila["rend_anual_%"]),
                    xytext=(6, 4), textcoords="offset points")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_xlabel("Volatilidad anual (%)")
    ax.set_ylabel("Rendimiento anual (%)")
    ax.set_title("Riesgo vs. rendimiento")
    _guardar(fig, "02_riesgo_rendimiento.png")
    return fig


def graficar_correlacion(precios: pd.DataFrame):
    corr = precios.pct_change(fill_method=None).corr()
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
                square=True, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlación de rendimientos diarios")
    _guardar(fig, "03_correlacion.png")
    return fig


def graficar_margenes(mg: pd.DataFrame):
    pivote = mg.pivot_table(index="anio", columns="empresa", values="margen_operativo_%")
    fig, ax = plt.subplots(figsize=(11, 6))
    pivote.plot(kind="bar", ax=ax, width=0.85)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Margen operativo por año (%)")
    ax.set_ylabel("%")
    ax.set_xlabel("")
    ax.legend(ncol=4, fontsize=8)
    _guardar(fig, "04_margen_operativo.png")
    return fig


def graficar_id(mg: pd.DataFrame):
    ultimo = mg.dropna(subset=["id_sobre_ingresos_%"]).sort_values("anio").groupby("empresa").last()
    ultimo = ultimo.sort_values("id_sobre_ingresos_%")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(ultimo.index, ultimo["id_sobre_ingresos_%"])
    for i, (v, a) in enumerate(zip(ultimo["id_sobre_ingresos_%"], ultimo["anio"])):
        ax.text(v, i, f" {v:.1f}% ({a})", va="center", fontsize=9)
    ax.set_title("Inversión en I+D como % de ingresos (último año disponible)")
    ax.set_xlabel("%")
    _guardar(fig, "05_inversion_id.png")
    return fig
