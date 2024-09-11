import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from dashboard.dados import (
    carregar_dados,
    enriquecer_df_renda_fixa,
    obter_valores_titulo,
    obter_resgates_titulo,
)
from src.dashboard.formatacao import formatar_df_renda_fixa, formatar_df_resgates
from src.dashboard.graficos import plotar_saldo_no_tempo


def pagina_renda_fixa(
    renda_fixa_df: pd.DataFrame,
    patrimonio_rf: pd.DataFrame,
    resgates_rf: pd.DataFrame,
):
    # Controles
    with st.sidebar:
        filtrar_invativos = st.checkbox("Mostrar inativos", value=False)
        if not filtrar_invativos:
            renda_fixa_df = renda_fixa_df[renda_fixa_df["status"].eq(1)]
        id_titulo = st.selectbox(
            "ID do título", ["Selecionar"] + renda_fixa_df["id"].unique().tolist()
        )

    df_rf_formatado = formatar_df_renda_fixa(renda_fixa_df, filtrar_invativos)

    st.subheader("Lista de títulos")
    st.dataframe(df_rf_formatado, hide_index=True, use_container_width=True)

    st.subheader("Rentabilidade")
    if id_titulo == "Selecionar":
        st.markdown("Selecione um título para ver a rentabilidade.")
    else:
        titulo_selecionado = df_rf_formatado.loc[
            df_rf_formatado["ID"].eq(id_titulo), :
        ].iloc[0]

        cols = st.columns(5)
        cols[0].metric("Rentabilidade", titulo_selecionado["Retorno"])
        cols[1].metric("Rendimentos", titulo_selecionado["Rendimentos"])
        cols[2].metric("Saldo", titulo_selecionado["Saldo"])
        cols[3].metric("Data de vencimento", titulo_selecionado["Vencimento"])
        cols[4].metric("Data de atualização", titulo_selecionado["Atualização"])

        st.html("<br>")
        cols = st.columns([2, 1])

        valores_titulo = obter_valores_titulo(patrimonio_rf, id_titulo)
        cols[0].markdown("##### Marcação na curva")
        cols[0].plotly_chart(plotar_saldo_no_tempo(valores_titulo))

        cols[1].markdown("##### Resgates")
        resgates_titulo = obter_resgates_titulo(resgates_rf, id_titulo)
        if resgates_titulo.empty:
            cols[1].markdown("Nenhum resgate encontrado.")
        else:
            cols[1].dataframe(formatar_df_resgates(resgates_titulo), hide_index=True)


st.set_page_config(
    page_title="Renda Fixa",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
renda_fixa_df = enriquecer_df_renda_fixa(dados["carteira_rf"], dados["aportes_rf"])
pagina_renda_fixa(renda_fixa_df, dados["patrimonio_rf"], dados["resgates_rf"])
