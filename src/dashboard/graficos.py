import locale

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

locale.setlocale(locale.LC_ALL, "pt_BR")


def plotar_proventos(proventos: pd.DataFrame, por_ativo=False):
    colunas_agrup = ["anomes"]
    if por_ativo:
        colunas_agrup.append("codigo")

    proventos_agg = proventos.groupby(colunas_agrup, as_index=False)["total"].sum()
    fig = px.bar(
        proventos_agg,
        x="anomes",
        y="total",
        color="codigo" if por_ativo else None,
        text_auto=False if por_ativo else True,
        labels={
            "anomes": "Data",
            "total": "Total (R$)",
            "codigo": "Código",
        },
        title="Proventos por mês",
        color_discrete_sequence=px.colors.qualitative.Plotly,
    )
    fig.update_xaxes(tickformat="%B, %Y", dtick="M1")
    fig.update_layout(hovermode="x unified")
    return fig


def plotar_saldo_no_tempo(valores_titulo: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=valores_titulo.index, y=valores_titulo["valor"], mode="lines+markers"
        )
    )
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Valor (R$)",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
