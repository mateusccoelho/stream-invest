import re
from datetime import date
from io import StringIO
from abc import ABC, abstractmethod

import requests
import pandas as pd
import yfinance as yf


class IndicadorAbstrato(ABC):
    @abstractmethod
    def extrair(self, data: date) -> float:
        pass


class IMAB5(IndicadorAbstrato):
    def extrair(self, data: date) -> float:
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
                "Dt_Ref": data.strftime("%d/%m/%Y"),
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


class VNA(IndicadorAbstrato):
    def extrair(self, data: date) -> float:
        resposta = requests.post(
            "https://www.anbima.com.br/informacoes/vna/vna-down.asp",
            data={
                "Data": data.strftime("%d%m%Y"),
                "escolha": "2",
                "Idioma": "PT",
                "saida": "txt",
                "Dt_Ref_Ver": "20240422",
                "Inicio": data.strftime("%d/%m/%Y"),
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


class CDI(IndicadorAbstrato):
    def __init__(self):
        self.serie = self.baixar_serie()

    def baixar_serie(self) -> pd.Series:
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

    def extrair(self, data: date) -> float:
        return self.serie.loc[data]


class TickerBolsa(IndicadorAbstrato):
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.serie = self.baixar_serie()

    def baixar_serie(self) -> pd.Series:
        cotacoes = yf.Ticker(self.ticker).history()
        cotacoes.index = cotacoes.index.map(lambda x: x.date())
        return cotacoes["Close"]

    def extrair(self, data: date) -> float:
        return self.serie.loc[data]
