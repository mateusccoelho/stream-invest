import sys
sys.path.append("../../")

import pandas as pd
import streamlit as st

from dashboard.dados import (
    carregar_dados,
)
# from src.dashboard.formatacao import formatar_df_renda_fixa, formatar_df_resgates
# from src.dashboard.graficos import plotar_saldo_no_tempo


def pagina_patrimonio(
    patrimonio_rf: pd.DataFrame, 
    patrimonio_rv: pd.DataFrame,
    carteira_rf: pd.DataFrame,
    carteira_rv: pd.DataFrame,
):
    st.markdown("# Patrimônio")

    



st.set_page_config(
    page_title="Renda Fixa",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
pagina_patrimonio(
    dados["patrimonio_rf"],
    dados["patrimonio_rv"],
    dados["carteira_rf"],
    dados["carteira_rv"],
)