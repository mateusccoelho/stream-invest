import sys
sys.path.append("../../")

import pandas as pd
import streamlit as st

from src.dashboard.dados import (
    carregar_dados,
    enriquecer_df_renda_var,
    enriquecer_df_renda_fixa,
    enriquecer_patrimonio_rf,
    enriquecer_patrimonio_rv,
    calcular_metricas,
    calcular_df_patrimonio_total,
)
from src.dashboard.formatacao import (
    formatar_df_renda_var,
    formatar_df_renda_fixa,
    formatar_dinheiro,
    formatar_porcentagem,
)
from src.dashboard.graficos import plotar_patrimonio_total


def mostrar_metricas(metricas: pd.DataFrame):
    titulo_metricas = ["Patrimônio", "Retorno", "Retorno (%)", "Quantidade de ativos"]
    cols = st.columns(4)
    cols[0].metric(titulo_metricas[0], formatar_dinheiro(metricas[0]))
    cols[1].metric(titulo_metricas[1], formatar_dinheiro(metricas[1]))
    cols[2].metric(titulo_metricas[2], formatar_porcentagem(metricas[2]))
    cols[3].metric(titulo_metricas[3], metricas[3])


def pagina_patrimonio(
    renda_fixa_df: pd.DataFrame, 
    renda_var_df: pd.DataFrame,
    patrimonio_total: pd.DataFrame,
):
    st.markdown("# Patrimônio")

    st.markdown("### Evolução")
    st.plotly_chart(plotar_patrimonio_total(patrimonio_total), use_container_width=True)

    st.markdown("### ETFs")
    etfs = renda_var_df.loc[renda_var_df["tipo_ativo"].eq("ETF")]
    mostrar_metricas(calcular_metricas(etfs, "rv"))
    st.dataframe(
        formatar_df_renda_var(etfs), 
        hide_index=True, 
        use_container_width=True
    )

    st.markdown("### FI-Infra")
    fiinfra = renda_var_df.loc[renda_var_df["tipo_ativo"].eq("FI-Infra")]
    mostrar_metricas(calcular_metricas(fiinfra, "rv"))
    st.dataframe(
        formatar_df_renda_var(fiinfra), 
        hide_index=True, 
        use_container_width=True
    )
    
    st.markdown("### Renda fixa")
    df_rf = renda_fixa_df.loc[renda_fixa_df["status"].eq(1)]
    mostrar_metricas(calcular_metricas(df_rf, "rf"))
    st.dataframe(
        formatar_df_renda_fixa(df_rf, inativos=False), 
        hide_index=True, 
        use_container_width=True
    )


st.set_page_config(
    page_title="Renda Fixa",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
renda_var_df = enriquecer_df_renda_var(
    ativos_rv=dados["ativos_rv"], 
    carteira_rv=dados["carteira_rv"]
)
renda_fixa_df = enriquecer_df_renda_fixa(dados["carteira_rf"], dados["aportes_rf"])
patrimonio_rv = enriquecer_patrimonio_rv(dados["ativos_rv"], dados["patrimonio_rv"])
patrimonio_rf = enriquecer_patrimonio_rf(dados["aportes_rf"], dados["patrimonio_rf"])
patrimonio_total = calcular_df_patrimonio_total(patrimonio_rf, patrimonio_rv)
pagina_patrimonio(
    renda_fixa_df,
    renda_var_df,
    patrimonio_total,
)