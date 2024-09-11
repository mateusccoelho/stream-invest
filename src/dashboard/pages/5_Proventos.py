from datetime import date, timedelta
import sys

sys.path.append("..")

import streamlit as st
import pandas as pd

from src.dashboard.dados import (
    carregar_dados,
    agrupar_proventos_por_ativo,
    enriquecer_df_proventos,
)
from src.dashboard.formatacao import (
    formatar_df_proventos,
    formatar_dinheiro,
    formatar_df_proventos_ativo,
)
from src.dashboard.graficos import plotar_proventos


def pagina_proventos(proventos: pd.DataFrame):
    with st.sidebar:
        periodo = st.selectbox(
            "Período", ["6 meses", "1 ano", "2 anos", "Personalizado"]
        )
        if periodo == "Personalizado":
            data_inicial = st.date_input("Início do período", value=None)

    if periodo == "6 meses":
        data_inicial = date.today() - timedelta(days=180)
    elif periodo == "1 ano":
        data_inicial = date.today() - timedelta(days=365)
    elif periodo == "2 anos":
        data_inicial = date.today() - timedelta(days=730)

    proventos_filt = proventos[proventos["dt_pag"] >= data_inicial]
    proventos_ativo = agrupar_proventos_por_ativo(proventos_filt)
    prov_ativo_form = formatar_df_proventos_ativo(proventos_ativo)
    proventos_form = formatar_df_proventos(proventos_filt)

    st.markdown("# Proventos")
    st.markdown("### Visão Geral")

    cols = st.columns(3)
    cols[0].metric("Total", formatar_dinheiro(proventos["total"].sum()))
    cols[1].metric("Total no período", formatar_dinheiro(proventos_filt["total"].sum()))
    cols[2].metric("Quantidade", proventos_filt["codigo"].nunique())

    agrup_por_ativo = st.checkbox("Agrupar por ativo")
    st.plotly_chart(plotar_proventos(proventos_filt, agrup_por_ativo))

    st.markdown("### Resumo dos ativos")
    st.dataframe(prov_ativo_form, hide_index=True, use_container_width=True)

    st.markdown("### Detalhes")
    st.dataframe(proventos_form, hide_index=True, use_container_width=True)


st.set_page_config(
    page_title="Proventos",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
proventos = enriquecer_df_proventos(
    dados["proventos"], dados["ativos_rv"], dados["carteira_rv"]
)
pagina_proventos(proventos)
