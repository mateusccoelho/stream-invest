from pathlib import Path
from datetime import date

import pandas as pd

from src.consolidacao_variavel import consolidar_renda_variavel
from src.consolidacao_fixa import consolidar_renda_fixa

CAMINHO_DADOS = Path(__file__).resolve().parent.parent / "dados"


def le_dados_excel(sheet: str = None) -> pd.DataFrame | dict[str, pd.DataFrame]:
    return pd.read_excel(
        CAMINHO_DADOS / "Investimentos.xlsx", sheet_name=sheet, engine="openpyxl"
    )


def tratar_proventos(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos = proventos.rename(
        columns={
            "Data pagamento": "dt_pag",
            "Tipo": "tipo",
            "Código": "codigo",
            "Quantidade": "qtd",
            "Valor": "valor",
        }
    ).sort_values(["dt_pag", "codigo"], ascending=False)
    proventos["dt_pag"] = proventos["dt_pag"].dt.date
    proventos["total"] = (proventos["qtd"] * proventos["valor"]).round(2)
    proventos["anomes"] = proventos["dt_pag"].apply(lambda x: date(x.year, x.month, 1))
    return proventos


def tratar_ativos_rv(ativos_rv: pd.DataFrame) -> pd.DataFrame:
    return ativos_rv.rename(
        columns={
            "Código": "codigo",
            "Tipo": "tipo_ativo",
            "Benchmark": "bench",
        }
    )


def tratar_transacoes_rv(transacoes_rv: pd.DataFrame) -> pd.DataFrame:
    transacoes_rv = (
        transacoes_rv.rename(
            columns={
                "Data": "data",
                "Código": "codigo",
                "Operação C/V": "tipo",
                "Quantidade": "qtd",
                "Preço": "preco",
                "Corretora": "corretora",
                "Taxas": "taxas",
            }
        )
        .sort_values(["codigo", "data"])
        .reset_index(drop=True)
    )
    transacoes_rv["data"] = transacoes_rv["data"].dt.date
    return transacoes_rv


def tratar_aportes_rf(aportes_rf: pd.DataFrame) -> pd.DataFrame:
    aportes_rf = aportes_rf.rename(
        columns={
            "ID": "id",
            "Valor": "valor",
            "Corretora": "corretora",
            "Emissor": "emissor",
            "Tipo": "tipo",
            "Forma": "forma",
            "Data compra": "data_compra",
            "Data vencimento": "data_venc",
            "Indexador": "index",
            "Taxa": "taxa",
            "Reserva": "reserva",
        }
    )
    for col in ["data_compra", "data_venc"]:
        aportes_rf[col] = aportes_rf[col].dt.date

    return aportes_rf


def tratar_resgates_rf(resgate_rf: pd.DataFrame) -> pd.DataFrame:
    resgate_rf = resgate_rf.rename(
        columns={
            "ID": "id",
            "Valor": "valor",
            "Data resgate": "data_resgate",
            "Final": "final",
        }
    )
    resgate_rf["data_resgate"] = resgate_rf["data_resgate"].dt.date
    return resgate_rf


def consolidar_carteira() -> dict[str, pd.DataFrame]:
    cotacoes = pd.read_parquet(CAMINHO_DADOS / "cotacoes.parquet")
    proventos = tratar_proventos(le_dados_excel("Proventos RV"))
    ativos_rv = tratar_ativos_rv(le_dados_excel("Ativos RV"))
    transacoes_rv = tratar_transacoes_rv(le_dados_excel("Transações RV"))
    patrimonio_rv, carteira_rv = consolidar_renda_variavel(transacoes_rv, cotacoes)
    aportes_rf = tratar_aportes_rf(le_dados_excel("Aportes RF"))
    resgates_rf = tratar_resgates_rf(le_dados_excel("Resgates RF"))
    patrimonio_rf, carteira_rf = consolidar_renda_fixa(
        aportes_rf, resgates_rf, cotacoes
    )

    return {
        "proventos": proventos,
        "ativos_rv": ativos_rv,
        "transacoes_rv": transacoes_rv,
        "patrimonio_rv": patrimonio_rv,
        "carteira_rv": carteira_rv,
        "aportes_rf": aportes_rf,
        "resgates_rf": resgates_rf,
        "patrimonio_rf": patrimonio_rf,
        "carteira_rf": carteira_rf,
    }


if __name__ == "__main__":
    consolidar_carteira()
