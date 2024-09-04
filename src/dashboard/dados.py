import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from src.consolidacao_carteira import consolidar_carteira


@st.cache_resource
def carregar_dados() -> dict[str, pd.DataFrame]:
    return consolidar_carteira()


@st.cache_resource
def agrupar_proventos_por_ativo(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos_ativo = proventos.groupby(["codigo", "tipo_ativo", "preco_medio"]).agg(
        total=pd.NamedAgg(column="total", aggfunc="sum"),
        qtd=pd.NamedAgg(column="codigo", aggfunc="count"),
        ultimo_pag=pd.NamedAgg(column="dt_pag", aggfunc="max"),
        total_unitario=pd.NamedAgg(column="valor", aggfunc="sum"),
    ).reset_index()
    proventos_ativo["yoc_periodo"] = (
        proventos_ativo["total_unitario"] / proventos_ativo["preco_medio"]
    )
    proventos_ativo = proventos_ativo.drop(columns=["total_unitario", "preco_medio"])
    return proventos_ativo


@st.cache_resource
def enriquecer_df_proventos(
    proventos: pd.DataFrame, ativos_rv: pd.DataFrame, carteira_rv: pd.DataFrame
) -> pd.DataFrame:
    df = (
        proventos.merge(ativos_rv, on="codigo", how="left")
        .merge(carteira_rv, on="codigo", how="left")
    )
    df["yoc_anualizado"] = (df["valor"] * 12) / df["preco_medio"]
    return df