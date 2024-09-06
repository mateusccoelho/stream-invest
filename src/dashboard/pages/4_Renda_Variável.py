import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from dashboard.dados import carregar_dados_gerais_rv
from dashboard.formatacao import formatar_df_renda_var


st.set_page_config(page_title="Renda Variável", layout="wide")

renda_var_df = carregar_dados_gerais_rv()

with st.sidebar:
    filtrar_invativos = st.checkbox("Mostrar invativos", value=False)
    if not filtrar_invativos:
        renda_fixa_df = renda_var_df[renda_var_df["status"].eq(1)]

df_formatado = formatar_df_renda_var(renda_var_df, filtrar_invativos)

st.subheader("Lista de ativos")
st.dataframe(df_formatado, hide_index=True)
