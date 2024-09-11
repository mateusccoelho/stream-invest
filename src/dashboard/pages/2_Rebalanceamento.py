import sys

sys.path.append("../../")

import streamlit as st
import pandas as pd

from src.dashboard.dados import (
    carregar_dados,
    enriquecer_dfs_carteira,
    criar_df_rebalanceamento,
)
from src.dashboard.formatacao import (
    formatar_df_rebalanceamento,
    formatar_dinheiro,
)


def pagina_rebalanceamento(carteira_rf: pd.DataFrame, carteira_rv: pd.DataFrame):
    st.markdown("# Rebalanceamento")
    cols = st.columns(3)
    ccs = cols[0].number_input(
        "Contas correntes", min_value=0.0, step=0.01, format="%.2f"
    )
    fundos = cols[1].number_input(
        "Fundos de previdência", min_value=0.0, step=0.01, format="%.2f"
    )
    aporte_geral = cols[2].number_input(
        "Aporte geral", min_value=0.0, step=0.01, format="%.2f"
    )

    aportes_cols = {
        "Títulos privados CDI": 0,
        "FI-Infra CDI": 0,
        "Títulos públicos IPCA": 1,
        "Títulos privados IPCA": 1,
        "FI-Infra IPCA": 1,
        "Títulos privados pré": 2,
        "Ações Brasil": 3,
        "Ações Mundo": 3,
    }
    aportes_vals = []
    with st.expander("Aportes individuais"):
        cols = st.columns(4)
        for nome, col_idx in aportes_cols.items():
            aportes_vals.append(
                cols[col_idx].number_input(
                    nome, min_value=0.0, step=0.01, format="%.2f"
                )
            )

    rebalanc = criar_df_rebalanceamento(
        carteira_rf, carteira_rv, aporte_geral, aportes_vals
    )
    rebalanc_form = formatar_df_rebalanceamento(rebalanc)
    reserva = carteira_rf.loc[carteira_rf["emissor"].eq("Itaú Unibanco"), "saldo"].sum()

    st.dataframe(rebalanc_form, hide_index=True, use_container_width=True)

    cols = st.columns(3)
    cols[0].metric(
        "Patrimônio total",
        formatar_dinheiro(rebalanc["valor_atual"].sum() + ccs + fundos + reserva),
    )
    cols[1].metric(
        "Patrimônio booglehead",
        formatar_dinheiro(rebalanc["valor_atual"].sum()),
    )
    cols[2].metric("Reserva", formatar_dinheiro(reserva))


st.set_page_config(
    page_title="Rebalanceamento",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
carteira_rf, carteira_rv = enriquecer_dfs_carteira(
    dados["ativos_rv"],
    dados["aportes_rf"],
    dados["carteira_rf"],
    dados["carteira_rv"],
)
pagina_rebalanceamento(carteira_rf, carteira_rv)
