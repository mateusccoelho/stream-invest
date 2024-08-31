import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from src.consolidar_carteira import consolidar_carteira


@st.cache_resource
def carregar_dados() -> dict[str, pd.DataFrame]:
    return consolidar_carteira()


@st.cache_resource
def agrupar_proventos_por_ativo(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos_ativo = proventos.groupby("codigo").agg(
        total=pd.NamedAgg(column="total", aggfunc="sum"),
        qtd=pd.NamedAgg(column="codigo", aggfunc="count"),
        ultimo_pag=pd.NamedAgg(column="dt_pag", aggfunc="max"),
    )
    return proventos_ativo
