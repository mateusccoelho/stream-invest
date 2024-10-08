import numpy as np
import pandas as pd

from indicadores import TickerBolsa
from src.consolidacao_carteira import le_dados_excel


def le_dados_indicadores() -> pd.DataFrame:
    return pd.read_excel(
        "dados/Investimentos - Restos.xlsx",
        sheet_name="Indicadores",
        engine="openpyxl",
    )


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
        valores = TickerBolsa(codigo + ".SA").serie
        df_ticker = (
            valores.reset_index()
            .assign(codigo=codigo, variacao=np.nan)
            .rename(columns={"Close": "valor", "Date": "data"})
            .filter(["data", "codigo", "valor", "variacao"])
        )
        df_ticker["variacao"] = df_ticker["valor"].pct_change(fill_method=None) + 1
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
