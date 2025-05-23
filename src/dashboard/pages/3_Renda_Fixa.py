import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from src.dashboard.dados import (
    carregar_dados,
    enriquecer_df_renda_fixa,
    obter_valores_titulo,
    obter_resgates_titulo,
    criar_df_taxas,
    calcular_metricas_rend,
)
from src.dashboard.formatacao import (
    formatar_df_renda_fixa,
    formatar_df_resgates,
    formatar_df_taxas,
    formatar_df_taxas_agg,
    formatar_dinheiro,
)
from src.dashboard.graficos import plotar_saldo_no_tempo, plotar_emissores
from src.dashboard.layout import mostrar_metricas


def pagina_renda_fixa(
    renda_fixa_df: pd.DataFrame,
    patrimonio_rf: pd.DataFrame,
    resgates_rf: pd.DataFrame,
    df_taxas: pd.DataFrame,
    df_taxas_agg: pd.DataFrame,
):
    # Controles
    with st.sidebar:
        filtrar_invativos = st.checkbox("Mostrar inativos", value=False)
        if not filtrar_invativos:
            renda_fixa_df = renda_fixa_df[renda_fixa_df["status"].eq(1)]

    df_rf_formatado = formatar_df_renda_fixa(renda_fixa_df, filtrar_invativos)

    st.markdown("# Renda Fixa")
    mostrar_metricas(calcular_metricas_rend(renda_fixa_df, "rf"))

    df_rf_formatado.insert(0, "", False)
    df_rf_editado = st.data_editor(
        df_rf_formatado, hide_index=True, use_container_width=True
    )

    st.markdown("### Estudo de taxas CDI")
    cols = st.columns([3, 2])
    cols[0].markdown("##### Detalhes")
    cols[0].dataframe(
        formatar_df_taxas(df_taxas), hide_index=True, use_container_width=True
    )
    cols[1].markdown("##### Agregado")
    cols[1].dataframe(
        formatar_df_taxas_agg(df_taxas_agg), hide_index=True, use_container_width=True
    )

    st.markdown("### Emissores")
    cols = st.columns(4)
    cols[0].metric("Quantidade", renda_fixa_df["emissor"].nunique())
    cols[1].metric(
        "Exposição máxima",
        formatar_dinheiro(renda_fixa_df.groupby("emissor")["saldo"].sum().max()),
    )
    st.plotly_chart(plotar_emissores(renda_fixa_df), use_container_width=True)

    st.markdown("### Rentabilidade")
    if df_rf_editado[""].sum() == 0:
        st.markdown("Selecione um título para ver a rentabilidade.")
    elif df_rf_editado[""].sum() > 1:
        st.markdown("Selecione apenas um título.")
    else:
        id_titulo = df_rf_editado.loc[df_rf_editado[""], "ID"].iloc[0]
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
df_taxas, df_taxas_agg = criar_df_taxas(renda_fixa_df)
pagina_renda_fixa(
    renda_fixa_df, dados["patrimonio_rf"], dados["resgates_rf"], df_taxas, df_taxas_agg
)
