import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from dashboard.dados import carregar_dados, enriquecer_df_renda_var
from dashboard.formatacao import formatar_df_renda_var


def pagina_renda_variavel(renda_var_df: pd.DataFrame):
    with st.sidebar:
        inativos = st.checkbox("Mostrar inativos", value=False)
        if not inativos:
            renda_var_df = renda_var_df[renda_var_df["qtd"].gt(0)]

    df_formatado = formatar_df_renda_var(renda_var_df, inativos)

    st.subheader("Lista de ativos")
    st.dataframe(df_formatado, hide_index=True, use_container_width=True)


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
pagina_renda_variavel(renda_var_df)
