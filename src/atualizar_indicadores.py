import sys

sys.path.append("../../")
import re
from datetime import date, timedelta
from io import StringIO

import requests
import pandas as pd
import yfinance as yf

from utils.calendario import le_dias_uteis, dia_util_anterior


def listar_dados_faltantes(indicador: str, dias: int) -> pd.Series:
    data_fim = date.today()
    data_inicio = data_fim - timedelta(days=dias)

    dias_uteis = le_dias_uteis()
    dias_uteis = dias_uteis[(dias_uteis >= data_inicio) & (dias_uteis <= data_fim)]

    results = (
        session.query(Cotacoes.data)
        .filter(Cotacoes.codigo == indicador, Cotacoes.data.in_(dias_uteis))
        .all()
    )

    datas_na_tabela = {result.data for result in results}
    return dias_uteis[~dias_uteis.isin(datas_na_tabela)]


# def valor_anterior_preenchido(
#     session: SessionType, indicador: str, data: date, considerar_pregao=False
# ) -> float:
#     dia_anterior = dia_util_anterior(data, considerar_pregao)
#     result = (
#         session.query(Cotacoes.valor)
#         .filter(Cotacoes.codigo == indicador, Cotacoes.data == dia_anterior)
#         .one()
#     )
#     return result.valor


# def atualizar_ativo_bolsa(ticker: str):
#     with Session() as session:
#         datas_faltantes = listar_dados_faltantes(session, ticker, 60)
#         if datas_faltantes.empty:
#             print(f"Não há dados faltantes em {ticker}")
#             return

#         df_precos = extract_ticker(ticker, datas_faltantes.iloc[0])
#         for data in datas_faltantes:
#             if data not in df_precos["Date"].values:
#                 print(f"Dado faltante para {ticker} em {data}")
#                 continue

#             valor = df_precos.loc[df_precos["Date"].eq(data), "Close"].iloc[0]
#             cotacao = Cotacoes(
#                 data=data,
#                 codigo=ticker,
#                 valor=valor,
#                 variacao=df_precos.loc[df_precos["Date"].eq(data), "Variacao"].iloc[0],
#             )
#             session.add(cotacao)
#             print(f"{ticker} em {data} atualizado para {valor}")

#         session.commit()


# def atualizar_cdi():
#     with Session() as session:
#         datas_faltantes = listar_dados_faltantes(session, "CDI", 60)
#         if datas_faltantes.empty:
#             print(f"Não há dados faltantes em CDI")
#             return

#         serie_fator_diario = extract_cdi()

#         for data in datas_faltantes:
#             if data not in serie_fator_diario:
#                 print(f"Dado faltante para CDI em {data}")
#                 continue

#             valor = serie_fator_diario.loc[data]
#             cotacao = Cotacoes(data=data, codigo="CDI", variacao=valor)
#             session.add(cotacao)
#             print(f"CDI em {data} atualizado para {valor}")

#         session.commit()


# def atualizar_ibov():
#     with Session() as session:
#         datas_faltantes = listar_dados_faltantes(session, "IBOV", 60)

#     if datas_faltantes.empty:
#         print(f"Não há dados faltantes em IBOV")
#         return

#     serie_ibov = extract_ibov()
#     for data in datas_faltantes:
#         if data not in serie_ibov:
#             print(f"Dado faltante para IBOV em {data}")
#             continue

#         valor = serie_ibov.loc[data]
#         with Session() as session:
#             valor_anterior = valor_anterior_preenchido(session, "IBOV", data, True)
#             cotacao = Cotacoes(
#                 data=data, codigo="IBOV", valor=valor, variacao=valor / valor_anterior
#             )
#             session.add(cotacao)
#             session.commit()

#         print(f"IBOV em {data} atualizado para {valor}")


def atualizar_indicadores_anbima(indicador: str):
    datas_faltantes = listar_dados_faltantes(indicador, 60)

    if datas_faltantes.empty:
        print(f"Não há dados faltantes em {indicador}")
        return
    
    mapa_funcoes = {
        "IMAB 5": extrair_imab5,
        "VNA": extrair_vna,
    }

    for data in datas_faltantes:
        valor = mapa_funcoes[indicador](data)

        if not valor:
            print(f"Dado faltante para {indicador} em {data}")
            continue

        
        valor_anterior = valor_anterior_preenchido(session, indicador, data)
        cotacao = Cotacoes(
            data=data,
            codigo=indicador,
            valor=valor,
            variacao=valor / valor_anterior,
        )

        print(f"{indicador} em {data} atualizado para {valor}")


def extrair_cdi() -> pd.Series:
    resposta = requests.get("https://www.portaldefinancas.com/js-tx/cdidiaria.js")
    resposta.raise_for_status()

    regex = re.compile(r"document\.write\('(<.+>)'\);")
    html_bruto = regex.search(resposta.text).group(1)

    # Adicionando tag <table> no começo para permitir leitura do pandas
    # sem erros
    html_bruto = "<table>" + html_bruto

    # read_html retorna uma lista (?), por isso pego sempre o primeiro elemento
    df = pd.read_html(StringIO(html_bruto), decimal=",", thousands=".")[0]

    for col in [0, 2, 4]:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%y")

    for col in [1, 3, 5]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    cdi_series = pd.concat(
        [
            df[[value]].set_index(df[date].dt.date).dropna().div(100)[value]
            for date, value in [(0, 1), (2, 3), (4, 5)]
        ]
    )
    cdi_series.sort_index(inplace=True)
    return cdi_series


def extrair_vna(data_ref: date) -> float:
    resposta = requests.post(
        "https://www.anbima.com.br/informacoes/vna/vna-down.asp",
        data={
            "Data": data_ref.strftime("%d%m%Y"),
            "escolha": "2",
            "Idioma": "PT",
            "saida": "txt",
            "Dt_Ref_Ver": "20240422",
            "Inicio": data_ref.strftime("%d/%m/%Y"),
        },
    )
    resposta.raise_for_status()

    try:
        df = pd.read_csv(
            StringIO(resposta.text),
            sep=";",
            decimal=",",
            encoding="latin1",
            thousands=".",
            skiprows=7,
        )
    except:
        return None

    vna = df.loc[df["Titulo"].eq("NTN-B"), "VNA"].iloc[0]
    return float(vna)


def extrair_ibov() -> pd.Series:
    ibov = yf.Ticker("^BVSP").history()
    ibov.index = ibov.index.map(lambda x: x.date())
    return ibov["Close"]


def extrair_ticker(ticker: str, data: date) -> pd.DataFrame:
    dia_anterior = dia_util_anterior(data, considerar_pregao=True)
    df = yf.download(ticker + ".SA", start=dia_anterior, rounding=True).reset_index()
    df["Date"] = df["Date"].dt.date
    df["Variacao"] = df["Close"].pct_change() + 1
    df = df.dropna()
    return df


def extrair_imab5(data_ref: date) -> float:
    resposta = requests.post(
        "https://www.anbima.com.br/informacoes/ima/ima-sh-down.asp",
        data={
            "Tipo": "",
            "DataRef": "",
            "Pai": "ima",
            "escolha": "2",
            "Idioma": "PT",
            "saida": "csv",
            "Dt_Ref_Ver": "20240308",
            "Dt_Ref": data_ref.strftime("%d/%m/%Y"),
        },
    )
    resposta.raise_for_status()

    try:
        df = pd.read_csv(
            StringIO(resposta.text),
            sep=";",
            decimal=",",
            encoding="latin1",
            thousands=".",
            skiprows=1,
            usecols=["Índice", "Data de Referência", "Número Índice"],
            date_format="%d/%m/%Y",
            parse_dates=["Data de Referência"],
        )
    except:
        return None

    imab5 = df.loc[df["Índice"].eq("IMA-B 5"), "Número Índice"].iloc[0]
    return float(imab5)


if __name__ == "__main__":
    pass
