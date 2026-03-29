from datetime import date

import pandas as pd
import pandera.pandas as pa

from src.consolidacao.consolidacao_variavel import consolidar_renda_variavel
from src.consolidacao.consolidacao_fixa import consolidar_renda_fixa
from src.database.schemas import CotacoesSchema, ProventosRVSchema
from src.consolidacao.schemas import ProventosTratadosSchema
from src.database.database import (
    ler_aportes_rf,
    ler_cotacoes,
    ler_resgates_rf,
    ler_transacoes_rv,
    ler_proventos_rv,
    ler_ativos_rv,
    ler_proporcoes,
)


@pa.check_output(ProventosTratadosSchema)
@pa.check_output(ProventosRVSchema)
def tratar_proventos(proventos: pd.DataFrame) -> pd.DataFrame:
    proventos = proventos.sort_values(["dt_pag", "codigo"], ascending=False)
    proventos["total"] = (proventos["qtd"] * proventos["valor"]).round(2)
    proventos["anomes"] = proventos["dt_pag"].apply(lambda x: date(x.year, x.month, 1))
    return proventos


@pa.check_output(CotacoesSchema)
def _calcular_variacoes(cotacoes: pd.DataFrame) -> pd.DataFrame:
    """Calcula a coluna 'variacao' via pct_change agrupado por codigo."""

    cotacoes = cotacoes.sort_values(["codigo", "data"])
    variacoes = cotacoes.groupby("codigo")["valor"].pct_change(fill_method=None) + 1
    linhas_sem_variacao = cotacoes["valor"].notnull() & cotacoes["variacao"].isnull()
    cotacoes.loc[linhas_sem_variacao, "variacao"] = variacoes[linhas_sem_variacao]
    return cotacoes


# O schema dos dataframes retornados está no arquivo diagrama_tabelas.drawio
def consolidar_carteira() -> dict[str, pd.DataFrame]:
    cotacoes = _calcular_variacoes(ler_cotacoes())
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