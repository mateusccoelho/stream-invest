from datetime import date
import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from src.dashboard.dados import (
    carregar_dados,
    enriquecer_df_renda_var,
    calcular_metricas_rend,
    calcular_metricas_trans_rv,
)
from src.dashboard.formatacao import (
    formatar_df_renda_var,
    formatar_transacoes_rv,
    formatar_dinheiro,
)
from src.dashboard.layout import mostrar_metricas


def mostrar_metricas_trans(metricas: tuple[int, date, float, float]):
    cols = st.columns(4)
    cols[0].metric("Quantidade de operações", metricas[0])
    cols[1].metric("Operação mais recente", metricas[1].strftime("%d/%m/%Y"))
    cols[2].metric("Valor investido", formatar_dinheiro(metricas[2]))
    cols[3].metric("Valor vendido", formatar_dinheiro(metricas[3]))


def pagina_renda_variavel(renda_var_df: pd.DataFrame, transacoes: pd.DataFrame):
    with st.sidebar:
        inativos = st.checkbox("Mostrar inativos", value=False)
        if not inativos:
            renda_var_df = renda_var_df[renda_var_df["qtd"].gt(0)]

    df_formatado = formatar_df_renda_var(renda_var_df, inativos)

    st.markdown("# Renda Variável")
    mostrar_metricas(calcular_metricas_rend(renda_var_df, "rv"))

    df_formatado.insert(0, "", False)
    df_editado = st.data_editor(df_formatado, hide_index=True, use_container_width=True)

    st.markdown("### Transações")
    if df_editado[""].sum() == 0:
        st.markdown("Selecione pelo menos um ativo para ver as transações.")
    else:
        ids_ativos = df_editado.loc[df_editado[""], "Código"].tolist()
        trans_id = transacoes[transacoes["codigo"].isin(ids_ativos)]

        mostrar_metricas_trans(calcular_metricas_trans_rv(trans_id))

        st.dataframe(
            formatar_transacoes_rv(trans_id), hide_index=True, use_container_width=True
        )


st.set_page_config(
    page_title="Renda Variável",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
renda_var_df = enriquecer_df_renda_var(
    ativos_rv=dados["ativos_rv"], carteira_rv=dados["carteira_rv"]
)
pagina_renda_variavel(renda_var_df, dados["transacoes_rv"])
