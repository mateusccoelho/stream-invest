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
    calcular_metricas_rend,
    calcular_df_patrimonio_total,
    calcular_mov_diaria,
    calcular_mov_mensal,
    calcular_metricas_mov,
    calcular_metricas_patr,
    calcular_rendimento_diario,
)
from src.dashboard.formatacao import (
    formatar_df_renda_var,
    formatar_df_renda_fixa,
    formatar_dinheiro,
    formatar_porcentagem,
)
from src.dashboard.graficos import (
    plotar_patrimonio_total,
    plotar_movimentacoes,
    plotar_rendimento,
)
from src.dashboard.layout import mostrar_metricas


def mostrar_metricas_patr(metricas: tuple[float, float, float]):
    cols = st.columns(4)
    cols[0].metric("Patrimônio atual", formatar_dinheiro(metricas[0]))
    cols[1].metric("Crescimento total", formatar_porcentagem(metricas[1]))
    cols[2].metric("Crescimento total anual", formatar_porcentagem(metricas[2]))
    cols[3].metric("Crescimento 1 ano", formatar_porcentagem(metricas[3]))


def pagina_patrimonio(
    renda_fixa_df: pd.DataFrame,
    renda_var_df: pd.DataFrame,
    patrimonio_total: pd.DataFrame,
    movimentacoes: pd.DataFrame,
    rendimento: pd.DataFrame,
):
    st.markdown("# Patrimônio")
    mostrar_metricas_patr(calcular_metricas_patr(patrimonio_total))

    por_ativo = st.checkbox("Mostrar por ativo")
    st.plotly_chart(
        plotar_patrimonio_total(patrimonio_total, por_ativo=por_ativo),
        use_container_width=True,
    )

    st.markdown("### ETFs")
    etfs = renda_var_df.loc[renda_var_df["tipo_ativo"].eq("ETF")]
    mostrar_metricas(calcular_metricas_rend(etfs, "rv"))
    st.dataframe(formatar_df_renda_var(etfs), hide_index=True, use_container_width=True)

    st.markdown("### FI-Infra")
    fiinfra = renda_var_df.loc[renda_var_df["tipo_ativo"].eq("FI-Infra")]
    mostrar_metricas(calcular_metricas_rend(fiinfra, "rv"))
    st.dataframe(
        formatar_df_renda_var(fiinfra), hide_index=True, use_container_width=True
    )

    st.markdown("### Renda fixa")
    df_rf = renda_fixa_df.loc[renda_fixa_df["status"].eq(1)]
    mostrar_metricas(calcular_metricas_rend(df_rf, "rf"))
    st.dataframe(
        formatar_df_renda_fixa(df_rf, inativos=False),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### Movimentações")
    cols = st.columns(4)
    titulos = ["Compras", "Vendas", "Total investido"]
    mov_mensal = calcular_mov_mensal(movimentacoes)
    for idx, metrica in enumerate(calcular_metricas_mov(mov_mensal)):
        cols[idx].metric(label=titulos[idx], value=formatar_dinheiro(metrica))

    st.plotly_chart(plotar_movimentacoes(mov_mensal), use_container_width=True)

    st.markdown("### Rendimento diário")
    st.plotly_chart(plotar_rendimento(rendimento), use_container_width=True)


st.set_page_config(
    page_title="Renda Fixa",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
renda_var_df = enriquecer_df_renda_var(
    ativos_rv=dados["ativos_rv"], carteira_rv=dados["carteira_rv"]
)
renda_fixa_df = enriquecer_df_renda_fixa(dados["carteira_rf"], dados["aportes_rf"])
patrimonio_rv = enriquecer_patrimonio_rv(dados["ativos_rv"], dados["patrimonio_rv"])
patrimonio_rf = enriquecer_patrimonio_rf(dados["aportes_rf"], dados["patrimonio_rf"])
patrimonio_total = calcular_df_patrimonio_total(patrimonio_rf, patrimonio_rv)
movimentacoes = calcular_mov_diaria(
    dados["aportes_rf"], dados["resgates_rf"], dados["transacoes_rv"]
)
rendimento = calcular_rendimento_diario(
    patrimonio_total, movimentacoes, dados["cotacoes"]
)
pagina_patrimonio(
    renda_fixa_df,
    renda_var_df,
    patrimonio_total,
    movimentacoes,
    rendimento,
)
