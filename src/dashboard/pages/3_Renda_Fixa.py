import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from dashboard.dados import (
    carregar_dados_rf,
    obter_valores_titulo,
    obter_resgates_titulo,
)
from dashboard.formatacao import formatar_df_renda_fixa
from dashboard.graficos import plotar_saldo_no_tempo


st.set_page_config(page_title="Renda Fixa", layout="wide")

renda_fixa_df = carregar_dados_rf()

with st.sidebar:
    filtrar_invativos = st.checkbox("Mostrar invativos", value=False)
    if not filtrar_invativos:
        renda_fixa_df = renda_fixa_df[renda_fixa_df["status"].eq(1)]
    id_titulo = st.selectbox(
        "ID do título", ["Selecionar"] + renda_fixa_df.index.tolist()
    )

df_rf_formatado = formatar_df_renda_fixa(renda_fixa_df, filtrar_invativos)

st.subheader("Lista de títulos")
st.dataframe(df_rf_formatado, hide_index=True)

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

    valores_titulo = obter_valores_titulo(id_titulo)
    st.plotly_chart(plotar_saldo_no_tempo(valores_titulo))

    # resgates_titulo = obter_resgates_titulo(id_titulo)
    # st.markdown("### Transações")
    # st.dataframe(resgates_titulo, hide_index=True)
