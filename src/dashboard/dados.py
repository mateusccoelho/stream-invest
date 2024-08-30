import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from db.definicao_tabelas import (
    Session,
    AportesRendaFixa,
    CarteiraRF,
    PatrimonioRF,
    ResgatesRF,
    AtivosRV,
    CarteiraRV,
)


@st.cache_data
def carregar_dados_rf():
    with Session() as session:
        linhas_aportes = session.query(AportesRendaFixa).all()
        linhas_carteira = session.query(CarteiraRF).all()

    aportes = (
        pd.DataFrame([aporte.__dict__ for aporte in linhas_aportes])
        .set_index("id_titulo")
        .drop(columns=["_sa_instance_state"])
    )
    carteira = (
        pd.DataFrame([titulo.__dict__ for titulo in linhas_carteira])
        .set_index("id_titulo")
        .drop(columns=["_sa_instance_state"])
    )
    renda_fixa_df = aportes.join(carteira)
    renda_fixa_df["retorno"] = (
        renda_fixa_df["rendimentos_bruto"] / renda_fixa_df["valor_aplicado"]
    )
    return renda_fixa_df


@st.cache_data
def obter_valores_titulo(id_titulo: int) -> pd.DataFrame:
    with Session() as session:
        linhas_patrimonio = (
            session.query(PatrimonioRF).filter_by(id_titulo=id_titulo).all()
        )

    patrimonio = (
        pd.DataFrame([patrimonio.__dict__ for patrimonio in linhas_patrimonio])
        .set_index("data")
        .drop(columns=["_sa_instance_state"])
    )
    return patrimonio


@st.cache_data
def obter_resgates_titulo(id_titulo: int) -> pd.DataFrame:
    with Session() as session:
        linhas_resgates = session.query(ResgatesRF).filter_by(id_titulo=id_titulo).all()

    resgates = pd.DataFrame([resgate.__dict__ for resgate in linhas_resgates])
    return resgates


@st.cache_data
def carregar_dados_gerais_rv():
    with Session() as session:
        linhas_ativos = session.query(AtivosRV).all()
        linhas_carteira = session.query(CarteiraRV).all()

    ativos = (
        pd.DataFrame([ativo.__dict__ for ativo in linhas_ativos])
        .set_index("codigo")
        .drop(columns=["_sa_instance_state"])
    )
    carteira = (
        pd.DataFrame([ativo.__dict__ for ativo in linhas_carteira])
        .set_index("codigo")
        .drop(columns=["_sa_instance_state"])
    )
    renda_var_df = ativos.join(carteira)
    return renda_var_df
