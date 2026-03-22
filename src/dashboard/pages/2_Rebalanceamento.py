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

APORTES_KEY = "aportes_individuais"


def _inicializar_estado():
    if APORTES_KEY not in st.session_state:
        st.session_state[APORTES_KEY] = {}


def _adicionar_aporte(classe: str, valor: float):
    st.session_state[APORTES_KEY][classe] = (
        st.session_state[APORTES_KEY].get(classe, 0.0) + valor
    )


def _limpar_aportes():
    st.session_state[APORTES_KEY] = {}


def pagina_rebalanceamento(
    carteira_rf: pd.DataFrame,
    carteira_rv: pd.DataFrame,
    proporcoes: pd.DataFrame,
):
    classes = proporcoes["classe"].tolist()
    _inicializar_estado()

    st.markdown("# Rebalanceamento")
    st.divider()

    # Aportes
    st.markdown("#### Aportes")
    input_cols = st.columns([2, 1, 1, 1])
    classe_sel = input_cols[0].selectbox(
        "Classe", options=["Geral"] + classes, label_visibility="collapsed"
    )
    valor_aporte = input_cols[1].number_input(
        "Valor", min_value=0.0, step=0.01, format="%.2f", label_visibility="collapsed"
    )
    if input_cols[2].button("➕ Adicionar", use_container_width=True):
        if valor_aporte > 0:
            _adicionar_aporte(classe_sel, valor_aporte)
    if input_cols[3].button("🗑️ Limpar", use_container_width=True):
        _limpar_aportes()

    aportes_dict = st.session_state[APORTES_KEY]
    if aportes_dict:
        resumo = pd.DataFrame(
            [{"Classe": k, "Valor": formatar_dinheiro(v)} for k, v in aportes_dict.items()]
        )
        st.dataframe(resumo, hide_index=True, use_container_width=True)
    else:
        st.caption("Nenhum aporte adicionado.")

    aporte_geral = aportes_dict.get("Geral", 0.0)
    aportes_vals = pd.Series({c: aportes_dict.get(c, 0.0) for c in classes})

    st.divider()

    # Tabela de rebalanceamento
    rebalanc = criar_df_rebalanceamento(
        carteira_rf, carteira_rv, aporte_geral, aportes_vals, proporcoes
    )
    rebalanc_form = formatar_df_rebalanceamento(rebalanc)
    reserva = carteira_rf.loc[carteira_rf["reserva"], "saldo"].sum()

    st.markdown("#### Tabela de rebalanceamento")
    st.dataframe(rebalanc_form, hide_index=True, use_container_width=True)

    st.divider()

    # Métricas e patrimônio externo
    st.markdown("#### Patrimônio total")
    extra_cols = st.columns(2)
    ccs = extra_cols[0].number_input(
        "Contas correntes", min_value=0.0, step=0.01, format="%.2f"
    )
    fundos = extra_cols[1].number_input(
        "Fundos de previdência", min_value=0.0, step=0.01, format="%.2f"
    )

    metric_cols = st.columns(3)
    metric_cols[0].metric(
        "Patrimônio total",
        formatar_dinheiro(rebalanc["valor_atual"].sum() + ccs + fundos + reserva),
    )
    metric_cols[1].metric(
        "Patrimônio booglehead",
        formatar_dinheiro(rebalanc["valor_atual"].sum()),
    )
    metric_cols[2].metric("Reserva", formatar_dinheiro(reserva))


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
pagina_rebalanceamento(carteira_rf, carteira_rv, dados["proporcoes"])
