from pathlib import Path
from datetime import date

import pandas as pd

from src.consolidacao_variavel import consolidar_renda_variavel

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
    proventos["anomes"] = proventos["dt_pag"].apply(
        lambda x: date(x.year, x.month, 1)
    )
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
    transacoes_rv = transacoes_rv.rename(
        columns={
            "Data": "data",
            "Código": "codigo",
            "Operação C/V": "tipo",
            "Quantidade": "qtd",
            "Preço": "preco",
            "Corretora": "corretora",
            "Taxas": "taxas",
        }
    ).sort_values(["codigo", "data"]).reset_index(drop=True)
    transacoes_rv["data"] = transacoes_rv["data"].dt.date
    return transacoes_rv


def consolidar_carteira() -> dict[str, pd.DataFrame]:
    cotacoes = pd.read_parquet(CAMINHO_DADOS / "cotacoes.parquet")
    proventos = tratar_proventos(le_dados_excel("Proventos RV"))
    ativos_rv = tratar_ativos_rv(le_dados_excel("Ativos RV"))
    transacoes_rv = tratar_transacoes_rv(le_dados_excel("Transações RV"))
    patrimonio_rv, carteira_rv = consolidar_renda_variavel(transacoes_rv, cotacoes)
    return {
        "proventos": proventos,
        "ativos_rv": ativos_rv,
        "transacoes_rv": transacoes_rv,
        "patrimonio_rv": patrimonio_rv,
        "carteira_rv": carteira_rv,
    }


if __name__ == "__main__":
    consolidar_carteira()
