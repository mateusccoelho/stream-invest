from pathlib import Path
from datetime import date

import pandas as pd

CAMINHO_DADOS = Path(__file__).resolve().parent.parent / "dados"


def le_dados_excel(sheet: str = None) -> pd.DataFrame | dict[str, pd.DataFrame]:
    return pd.read_excel(
        CAMINHO_DADOS / "Investimentos.xlsx", sheet_name=sheet, engine="openpyxl"
    )


def tratar_proventos(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos = proventos.sort_values(["dt_pag", "codigo"], ascending=False).rename(
        columns={
            "Data pagamento": "dt_pag",
            "Tipo": "tipo",
            "Código": "codigo",
            "Quantidade": "qtd",
            "Valor": "valor",
        }
    )
    proventos["dt_pag"] = proventos["dt_pag"].dt.date
    proventos["total"] = (proventos["qtd"] * proventos["valor"]).round(2)
    proventos["anomes"] = proventos["dt_pag"].apply(lambda x: date(x.year, x.month, 1))
    return proventos


def consolidar_carteira() -> dict[str, pd.DataFrame]:
    proventos = le_dados_excel("Proventos RV")
    proventos = tratar_proventos(proventos)
    return {"proventos": proventos}


if __name__ == "__main__":
    consolidar_carteira()
