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
        retorno_valor = patrimonio - investido
    elif tipo == "rf":
        patrimonio = df["saldo"].sum()
        investido = df["valor"].sum()
        retorno_valor = df["rendimentos_bruto"].sum()
    
    retorno_porcent = retorno_valor / investido
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


@st.cache_resource
def calcular_mov_mensal(
    aportes_rf: pd.DataFrame, resgates_rf: pd.DataFrame, transacoes_rv: pd.DataFrame
):
    aportes_rf["data_compra"] = pd.to_datetime(aportes_rf["data_compra"])
    aportes_rf["data_compra"] = aportes_rf["data_compra"].dt.to_period("M").dt.to_timestamp()
    aportes_rf_mensal = aportes_rf.groupby("data_compra", as_index=False)["valor"].sum()
    aportes_rf_mensal.insert(1, "tipo", "compra")
    aportes_rf_mensal = aportes_rf_mensal.rename(columns={"data_compra": "data", "valor": "valor_trans"})
    
    resgates_rf["data_resgate"] = pd.to_datetime(resgates_rf["data_resgate"])
    resgates_rf["data_resgate"] = resgates_rf["data_resgate"].dt.to_period("M").dt.to_timestamp()
    resgates_rf_mensal = resgates_rf.groupby("data_resgate", as_index=False)["valor"].sum()
    resgates_rf_mensal.insert(1, "tipo", "venda")
    resgates_rf_mensal = resgates_rf_mensal.rename(columns={"data_resgate": "data", "valor": "valor_trans"})

    transacoes_rv["data"] = pd.to_datetime(transacoes_rv["data"])
    transacoes_rv["data"] = transacoes_rv["data"].dt.to_period("M").dt.to_timestamp()
    transacoes_rv_mensal = transacoes_rv.groupby(["data", "tipo"], as_index=False)["valor_trans"].sum()
    transacoes_rv_mensal["tipo"] = transacoes_rv_mensal["tipo"].replace({"C": "compra", "V": "venda"})

    movimentacoes = pd.concat([aportes_rf_mensal, resgates_rf_mensal, transacoes_rv_mensal])
    movimentacoes = movimentacoes.groupby(["data", "tipo"], as_index=False)["valor_trans"].sum()
    return movimentacoes


@st.cache_resource
def criar_df_taxas(df_fixa: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    def aliquota_ir(x: int):
        if x <= 180:
            return 0.225
        elif x <= 360:
            return 0.2
        elif x <= 720:
            return 0.175
        else:
            return 0.15

    df_taxas = df_fixa.loc[
        df_fixa["status"].eq(1) & df_fixa["index"].eq("CDI") & df_fixa["reserva"].eq(False),
        ["id", "tipo", "data_compra", "data_venc", "taxa", "valor"]
    ].copy()

    for col in ["data_compra", "data_venc"]:
        df_taxas[col] = pd.to_datetime(df_taxas[col])

    df_taxas["prazo_dias"] = (df_taxas["data_venc"] - df_taxas["data_compra"]).dt.days
    df_taxas["aliquota_ir"] = df_taxas["prazo_dias"].apply(aliquota_ir)
    df_taxas["faixa_prazo"] = pd.cut(
        df_taxas["prazo_dias"],
        bins=[0, 180, 360, 720, 9999],
        labels=["até 180 dias", "181 a 360 dias", "361 a 720 dias", "mais de 720 dias"],
    )
    df_taxas.loc[df_taxas["tipo"].isin(["LCA", "LCI"]), "aliquota_ir"] = 0
    df_taxas["taxa_desc"] = df_taxas["taxa"] * (1 - df_taxas["aliquota_ir"])
    df_taxas["valor_taxa"] = df_taxas["valor"] * df_taxas["taxa_desc"]

    df_taxas_agg = df_taxas.groupby("faixa_prazo", as_index=False).agg(
        valor=pd.NamedAgg(column="valor", aggfunc="sum"),
        valor_taxa=pd.NamedAgg(column="valor_taxa", aggfunc="sum"),
    )
    df_taxas_agg["proporcao"] = df_taxas_agg["valor"] / df_taxas_agg["valor"].sum()
    df_taxas_agg["taxa_media"] = df_taxas_agg["valor_taxa"] / df_taxas_agg["valor"]
    df_taxas_agg["taxa_alvo"] = df_taxas_agg["taxa_media"] / (1 - pd.Series([0.225, 0.2, 0.175, 0.15]))

    df_taxas = df_taxas.drop(columns=["aliquota_ir", "data_compra", "data_venc", "valor_taxa"])
    df_taxas_agg = df_taxas_agg.drop(columns=["valor_taxa"])
    return df_taxas, df_taxas_agg
