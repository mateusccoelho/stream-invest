from datetime import date

import numpy as np
import pandas as pd

from indicadores import extrair_ticker


def cria_df_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date
    df = df.set_index("Data").dropna(how="all")

    indicadores = {
        "VNA": ["VNA", "Fator VNA"],
        "IBOV": ["IBOV", "Fator IBOV"],
        "IMAB 5": ["IMAB 5", "Fator IMAB 5"],
    }

    dfs_indicadores = []
    for nome, colunas in indicadores.items():
        df_ind = (
            df[colunas]
            .dropna(how="all")
            .reset_index()
            .assign(codigo=nome)
            .rename(columns={nome: "valor", colunas[1]: "variacao", "Data": "data"})
            .filter(["data", "codigo", "valor", "variacao"])
        )
        dfs_indicadores.append(df_ind)

    dfs_indicadores.append(
        df[["CDI"]]
        .dropna(how="all")
        .reset_index()
        .assign(codigo="CDI", valor=np.nan)
        .rename(columns={"CDI": "variacao", "Data": "data"})
        .filter(["data", "codigo", "valor", "variacao"])
    )

    cotacoes = pd.concat(dfs_indicadores).rename(columns={"Data": "data"})
    return cotacoes


def cria_parquet_cotacoes():
    ativos = le_dados_excel("Ativos RV")
    codigos = ativos["Código"].unique()

    dfs_tickers = []
    for codigo in codigos:
        df_ticker = extrair_ticker(codigo, date(2024, 1, 2))
        df_ticker = (
            df_ticker.assign(codigo=codigo)
            .rename(columns={"Close": "valor", "Date": "data", "Variacao": "variacao"})
            .filter(["data", "codigo", "valor", "variacao"])
        )
        dfs_tickers.append(df_ticker)

    cotacoes_bolsa = pd.concat(dfs_tickers)

    df_indicadores_historico = le_dados_indicadores()
    cotacoes_indicadores = cria_df_indicadores(df_indicadores_historico)

    cotacoes = pd.concat([cotacoes_indicadores, cotacoes_bolsa]).sort_values(
        ["codigo", "data"]
    )

    cotacoes.to_parquet("dados/cotacoes.parquet", index=False)


if __name__ == "__main__":
    cria_parquet_cotacoes()
