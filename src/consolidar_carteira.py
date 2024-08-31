from pathlib import Path
from datetime import date

import pandas as pd

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
    return ativos_rv.rename(columns={
        "Código": "codigo",
        "Tipo": "tipo_ativo",
        "Benchmark": "bench",
    })


def consolidar_carteira() -> dict[str, pd.DataFrame]:
    proventos = tratar_proventos(le_dados_excel("Proventos RV"))
    ativos_rv = tratar_ativos_rv(le_dados_excel("Ativos RV"))
    return {"proventos": proventos, "ativos_rv": ativos_rv}


if __name__ == "__main__":
    consolidar_carteira()
