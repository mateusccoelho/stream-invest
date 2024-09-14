import locale

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.constants import CATEGORIAS_ATIVOS

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


def plotar_patrimonio_total(patrimonio: pd.DataFrame, por_ativo=False):
    patrimonio["classe"] = patrimonio["classe"].replace(CATEGORIAS_ATIVOS)
    patrimonio["data"] = pd.to_datetime(patrimonio["data"])
    patrimonio["data"] = patrimonio["data"].dt.to_period("M").dt.to_timestamp()
    patr_mensal = patrimonio.groupby(["data", "classe"], as_index=False)["saldo"].last()
    
    if por_ativo:
        fig = px.bar(
            patr_mensal,
            x="data",
            y="saldo",
            color="classe",
            labels={"data": "Data", "saldo": "Saldo (R$)", "classe": "Classe"},
            hover_data={"saldo": ":.2f"},
        )
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ))
    else:
        patr_mensal_total = patr_mensal.groupby("data", as_index=False).sum()
        fig = px.line(
            patr_mensal_total,
            x="data",
            y="saldo",
            labels={"data": "Data", "saldo": "Saldo (R$)"},
            markers=True,
        )
        
    fig.update_traces(hovertemplate=None)
    fig.update_xaxes(tickformat="%m/%y", dtick="M2")
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
    )
    return fig
