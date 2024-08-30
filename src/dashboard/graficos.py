import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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
        title="Marcação na curva",
    )
    return fig
