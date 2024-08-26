import sys

sys.path.append("..")
import re
from datetime import date, timedelta
from io import StringIO

import requests
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session as SessionType

from definicao_tabelas import Session, Cotacoes
from utils.calendario import le_dias_uteis, dia_util_anterior


def listar_dados_faltantes(
    session: SessionType, indicador: str, dias: int
) -> pd.Series:
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


def valor_anterior_preenchido(
    session: SessionType, indicador: str, data: date, considerar_pregao=False
) -> float:
    dia_anterior = dia_util_anterior(data, considerar_pregao)
    result = (
        session.query(Cotacoes.valor)
        .filter(Cotacoes.codigo == indicador, Cotacoes.data == dia_anterior)
        .one()
    )
    return result.valor


def atualizar_ativo_bolsa(ticker: str):
    with Session() as session:
        datas_faltantes = listar_dados_faltantes(session, ticker, 60)
        if datas_faltantes.empty:
            print(f"Não há dados faltantes em {ticker}")
            return

        df_precos = extract_ticker(ticker, datas_faltantes.iloc[0])
        for data in datas_faltantes:
            if data not in df_precos["Date"].values:
                print(f"Dado faltante para {ticker} em {data}")
                continue

            valor = df_precos.loc[df_precos["Date"].eq(data), "Close"].iloc[0]
            cotacao = Cotacoes(
                data=data,
                codigo=ticker,
                valor=valor,
                variacao=df_precos.loc[df_precos["Date"].eq(data), "Variacao"].iloc[0],
            )
            session.add(cotacao)
            print(f"{ticker} em {data} atualizado para {valor}")

        session.commit()


def atualizar_cdi():
    with Session() as session:
        datas_faltantes = listar_dados_faltantes(session, "CDI", 60)
        if datas_faltantes.empty:
            print(f"Não há dados faltantes em CDI")
            return

        serie_fator_diario = extract_cdi()

        for data in datas_faltantes:
            if data not in serie_fator_diario:
                print(f"Dado faltante para CDI em {data}")
                continue

            valor = serie_fator_diario.loc[data]
            cotacao = Cotacoes(data=data, codigo="CDI", variacao=valor)
            session.add(cotacao)
            print(f"CDI em {data} atualizado para {valor}")

        session.commit()


def atualizar_ibov():
    with Session() as session:
        datas_faltantes = listar_dados_faltantes(session, "IBOV", 60)

    if datas_faltantes.empty:
        print(f"Não há dados faltantes em IBOV")
        return

    serie_ibov = extract_ibov()
    for data in datas_faltantes:
        if data not in serie_ibov:
            print(f"Dado faltante para IBOV em {data}")
            continue

        valor = serie_ibov.loc[data]
        with Session() as session:
            valor_anterior = valor_anterior_preenchido(session, "IBOV", data, True)
            cotacao = Cotacoes(
                data=data, codigo="IBOV", valor=valor, variacao=valor / valor_anterior
            )
            session.add(cotacao)
            session.commit()

        print(f"IBOV em {data} atualizado para {valor}")


def atualizar_indicadores_anbima(indicador: str):
    with Session() as session:
        datas_faltantes = listar_dados_faltantes(session, indicador, 60)

    if datas_faltantes.empty:
        print(f"Não há dados faltantes em IBOV")
        return

    for data in datas_faltantes:
        func = extract_imab5 if indicador == "IMAB 5" else extract_vna
        valor = func(data)

        if not valor:
            print(f"Dado faltante para {indicador} em {data}")
            continue

        with Session() as session:
            valor_anterior = valor_anterior_preenchido(session, indicador, data)
            cotacao = Cotacoes(
                data=data,
                codigo=indicador,
                valor=valor,
                variacao=valor / valor_anterior,
            )
            session.add(cotacao)
            session.commit()

        print(f"{indicador} em {data} atualizado para {valor}")


def extract_cdi() -> pd.Series:
    response = requests.get("https://www.portaldefinancas.com/js-tx/cdidiaria.js")
    response.raise_for_status()

    pattern = re.compile(r"document\.write\('(<.+>)'\);")
    raw_html = pattern.search(response.text).group(1)

    # Adicionando tag <table> no começo para permitir leitura do pandas
    # sem erros
    raw_html = "<table>" + raw_html

    # read_html retorna uma lista (?), por isso pego sempre o primeiro elemento
    df = pd.read_html(StringIO(raw_html), decimal=",", thousands=".")[0]

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


def extract_vna(ref_date: date) -> float:
    response = requests.post(
        "https://www.anbima.com.br/informacoes/vna/vna-down.asp",
        data={
            "Data": ref_date.strftime("%d%m%Y"),
            "escolha": "2",
            "Idioma": "PT",
            "saida": "txt",
            "Dt_Ref_Ver": "20240422",
            "Inicio": ref_date.strftime("%d/%m/%Y"),
        },
    )
    response.raise_for_status()

    try:
        df = pd.read_csv(
            StringIO(response.text),
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


def extract_ibov() -> pd.Series:
    ibov = yf.Ticker("^BVSP").history()
    ibov.index = ibov.index.map(lambda x: x.date())
    return ibov["Close"]


def extract_ticker(ticker: str, data: date) -> pd.Series:
    dia_anterior = dia_util_anterior(data, considerar_pregao=True)
    df = yf.download(ticker + ".SA", start=dia_anterior, rounding=True).reset_index()
    df["Date"] = df["Date"].dt.date
    df["Variacao"] = df["Close"].pct_change() + 1
    df = df.dropna()
    return df


def extract_imab5(date_ref: date) -> float:
    response = requests.post(
        "https://www.anbima.com.br/informacoes/ima/ima-sh-down.asp",
        data={
            "Tipo": "",
            "DataRef": "",
            "Pai": "ima",
            "escolha": "2",
            "Idioma": "PT",
            "saida": "csv",
            "Dt_Ref_Ver": "20240308",
            "Dt_Ref": date_ref.strftime("%d/%m/%Y"),
        },
    )
    response.raise_for_status()

    try:
        df = pd.read_csv(
            StringIO(response.text),
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
    atualizar_cdi()
    atualizar_ibov()
    atualizar_indicadores_anbima("VNA")
    atualizar_indicadores_anbima("IMAB 5")
    atualizar_ativo_bolsa("B5P211")
    atualizar_ativo_bolsa("PIBB11")
    atualizar_ativo_bolsa("ACWI11")
    atualizar_ativo_bolsa("JURO11")
    atualizar_ativo_bolsa("CDII11")
    pass
