from datetime import date

import pandas as pd

from src.consolidacao_variavel import consolidar_renda_variavel
from src.consolidacao_fixa import consolidar_renda_fixa
from src.database import (
    CAMINHO_DADOS,
    ler_aportes_rf,
    ler_resgates_rf,
    ler_transacoes_rv,
    ler_proventos_rv,
    ler_ativos_rv,
    ler_proporcoes,
)


def tratar_proventos(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos = proventos.sort_values(["dt_pag", "codigo"], ascending=False)
    proventos["total"] = (proventos["qtd"] * proventos["valor"]).round(2)
    proventos["anomes"] = proventos["dt_pag"].apply(lambda x: date(x.year, x.month, 1))
    return proventos


# O schema dos dataframes retornados está no arquivo diagrama_tabelas.drawio
def consolidar_carteira() -> dict[str, pd.DataFrame]:
    cotacoes = pd.read_parquet(CAMINHO_DADOS / "cotacoes.parquet")
    proventos = tratar_proventos(ler_proventos_rv())
    ativos_rv = ler_ativos_rv()
    transacoes_rv = ler_transacoes_rv()
    patrimonio_rv, carteira_rv = consolidar_renda_variavel(transacoes_rv, cotacoes)
    aportes_rf = ler_aportes_rf()
    resgates_rf = ler_resgates_rf()
    patrimonio_rf, carteira_rf = consolidar_renda_fixa(
        aportes_rf, resgates_rf, cotacoes
    )
    proporcoes = ler_proporcoes()

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
        "cotacoes": cotacoes,
        "proporcoes": proporcoes,
    }


if __name__ == "__main__":
    consolidar_carteira()
