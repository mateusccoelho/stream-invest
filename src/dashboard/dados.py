import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from src.consolidacao_carteira import consolidar_carteira


@st.cache_resource
def carregar_dados() -> dict[str, pd.DataFrame]:
    return consolidar_carteira()


@st.cache_resource
def enriquecer_df_renda_fixa(
    carteira_rf: pd.DataFrame, aportes_rf: pd.DataFrame
) -> pd.DataFrame:
    df = carteira_rf.merge(aportes_rf, on="id", how="left")
    df["retorno"] = df["rendimentos_bruto"] / df["valor"]
    return df


@st.cache_resource
def enriquecer_df_renda_var(
    ativos_rv: pd.DataFrame, carteira_rv: pd.DataFrame
) -> pd.DataFrame:
    df = ativos_rv.merge(carteira_rv, on="codigo", how="inner")
    df["retorno"] = df["rendimento_total"] / (df["preco_medio"] * df["qtd"])
    df["preco_atual"] = df["patrimonio"] / df["qtd"]
    return df


def obter_valores_titulo(patrimonio_rf: pd.DataFrame, id_titulo: int) -> pd.DataFrame:
    return patrimonio_rf.loc[patrimonio_rf["id"].eq(id_titulo)].set_index("data")


def obter_resgates_titulo(resgates_rf: pd.DataFrame, id_titulo: int) -> pd.DataFrame:
    return resgates_rf.loc[resgates_rf["id"].eq(id_titulo)]


@st.cache_resource
def agrupar_proventos_por_ativo(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos_ativo = (
        proventos.groupby(["codigo", "tipo_ativo", "preco_medio"])
        .agg(
            total=pd.NamedAgg(column="total", aggfunc="sum"),
            qtd=pd.NamedAgg(column="codigo", aggfunc="count"),
            ultimo_pag=pd.NamedAgg(column="dt_pag", aggfunc="max"),
            total_unitario=pd.NamedAgg(column="valor", aggfunc="sum"),
        )
        .reset_index()
    )
    proventos_ativo["yoc_periodo"] = (
        proventos_ativo["total_unitario"] / proventos_ativo["preco_medio"]
    )
    proventos_ativo = proventos_ativo.drop(columns=["total_unitario", "preco_medio"])
    return proventos_ativo


@st.cache_resource
def enriquecer_df_proventos(
    proventos: pd.DataFrame, ativos_rv: pd.DataFrame, carteira_rv: pd.DataFrame
) -> pd.DataFrame:
    df = proventos.merge(ativos_rv, on="codigo", how="left").merge(
        carteira_rv, on="codigo", how="left"
    )
    df["yoc_anualizado"] = (df["valor"] * 12) / df["preco_medio"]
    return df


@st.cache_resource
def enriquecer_dfs_carteira(
    ativos_rv: pd.DataFrame,
    aportes_rf: pd.DataFrame,
    carteira_rf: pd.DataFrame,
    carteira_rv: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    carteira_rv = carteira_rv.loc[carteira_rv["qtd"].gt(0)].merge(
        ativos_rv, on="codigo", how="left"
    )
    carteira_rf = carteira_rf.loc[carteira_rf["status"].ge(1)].merge(
        aportes_rf, on="id", how="left"
    )
    return carteira_rf, carteira_rv


def criar_df_rebalanceamento(
    carteira_rf: pd.DataFrame,
    carteira_rv: pd.DataFrame,
    aporte_geral: float,
    aportes_vals: list[float],
) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "tipo": [
                "titulos_priv_cdi",
                "fi_infra_cdi",
                "titulos_pub_ipca",
                "titulos_priv_ipca",
                "fi_infra_ipca",
                "titulos_priv_pre",
                "acoes_br",
                "acoes_mundo",
            ],
            "porcent_alvo": [0.3, 0.1, 0.15, 0.1, 0.1, 0.05, 0.1, 0.1],
            "valor_atual": [
                carteira_rf.loc[
                    carteira_rf["index"].eq("CDI") & (~carteira_rf["reserva"]),
                    "saldo",
                ].sum(),
                carteira_rv.loc[
                    carteira_rv["tipo_ativo"].eq("FI-Infra")
                    & carteira_rv["bench"].eq("CDI"),
                    "patrimonio",
                ].sum(),
                carteira_rv.loc[
                    carteira_rv["tipo_ativo"].eq("ETF")
                    & carteira_rv["bench"].eq("IMAB 5"),
                    "patrimonio",
                ].sum(),
                carteira_rf.loc[carteira_rf["index"].eq("IPCA +"), "saldo"].sum(),
                carteira_rv.loc[
                    carteira_rv["tipo_ativo"].eq("FI-Infra")
                    & carteira_rv["bench"].eq("IMAB 5"),
                    "patrimonio",
                ].sum(),
                carteira_rf.loc[carteira_rf["index"].eq("Pré"), "saldo"].sum(),
                carteira_rv.loc[carteira_rv["codigo"].eq("PIBB11"), "patrimonio"].sum(),
                carteira_rv.loc[carteira_rv["codigo"].eq("ACWI11"), "patrimonio"].sum(),
            ],
        }
    )
    df["porcent_atual"] = df["valor_atual"] / df["valor_atual"].sum()

    total_com_aportes = df["valor_atual"].sum() + aporte_geral + sum(aportes_vals)
    df["valor_alvo"] = df["porcent_alvo"] * total_com_aportes

    valor_com_aportes = df["valor_atual"] + pd.Series(aportes_vals)
    # A lista de aportes individuais tem que estar na mesma ordem da tabela de
    # rebalanceamento para que a conta funcione.
    df["delta"] = df["valor_alvo"] - valor_com_aportes

    return df


@st.cache_resource
def enriquecer_patrimonio_rf(
    aportes_rf: pd.DataFrame, patrimonio_rf: pd.DataFrame
) -> pd.DataFrame:
    return patrimonio_rf.merge(
        aportes_rf[["id", "index", "emissor"]], on="id", how="left"
    )


@st.cache_resource
def enriquecer_patrimonio_rv(
    ativos_rv: pd.DataFrame, patrimonio_rv: pd.DataFrame
) -> pd.DataFrame:
    return patrimonio_rv.merge(ativos_rv, on="codigo", how="left")


@st.cache_resource
def calcular_metricas(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    if tipo == "rv":
        patrimonio = df["patrimonio"].sum()
        investido = (df["preco_medio"] * df["qtd"]).sum()
    elif tipo == "rf":
        patrimonio = df["saldo"].sum()
        investido = df["valor"].sum()

    retorno_valor = patrimonio - investido
    retorno_porcent = (patrimonio - investido) / investido
    qtd = df.shape[0]
    return patrimonio, retorno_valor, retorno_porcent, qtd


@st.cache_resource
def calcular_df_patrimonio_total(
    patrimonio_rf: pd.DataFrame, patrimonio_rv: pd.DataFrame
) -> pd.DataFrame:
    patrimonio_rf_agg = patrimonio_rf.groupby(["data", "index"], as_index=False).agg(
        saldo=pd.NamedAgg(column="valor", aggfunc="sum")
    )

    patrimonio_rf_agg["classe"] = patrimonio_rf_agg["index"].replace(
        {
            "IPCA +": "titulos_priv_ipca",
            "Pré": "titulos_priv_pre",
            "CDI": "titulos_priv_cdi",
        }
    )

    patrimonio_rv_agg = patrimonio_rv.groupby(
        ["data", "tipo_ativo", "bench"], as_index=False
    ).agg(saldo=pd.NamedAgg(column="patrimonio", aggfunc="sum"))

    patrimonio_rv_agg["classe"] = ""
    patrimonio_rv_agg.loc[
        patrimonio_rv_agg["tipo_ativo"].eq("FI-Infra")
        & patrimonio_rv_agg["bench"].eq("CDI"),
        "classe",
    ] = "fi_infra_cdi"
    patrimonio_rv_agg.loc[
        patrimonio_rv_agg["tipo_ativo"].eq("ETF")
        & patrimonio_rv_agg["bench"].eq("IMAB 5"),
        "classe",
    ] = "titulos_pub_ipca"
    patrimonio_rv_agg.loc[
        patrimonio_rv_agg["tipo_ativo"].eq("FI-Infra")
        & patrimonio_rv_agg["bench"].eq("IMAB 5"),
        "classe",
    ] = "fi_infra_ipca"
    patrimonio_rv_agg.loc[
        patrimonio_rv_agg["tipo_ativo"].eq("ETF")
        & patrimonio_rv_agg["bench"].eq("IBOV"),
        "classe",
    ] = "acoes"

    filter_list = ["data", "classe", "saldo"]
    patrimonio_total = pd.concat(
        [patrimonio_rf_agg[filter_list], patrimonio_rv_agg[filter_list]]
    )
    return patrimonio_total
