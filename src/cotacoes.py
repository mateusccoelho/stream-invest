from datetime import date, timedelta
from typing import Iterable

import pandas as pd
import numpy as np

from utils.calendario import calcular_dias_uteis_entre
from indicadores import IMAB5, VNA, TickerBolsa, CDI, IndicadorAbstrato


class Cotacoes:
    def __init__(self, cotacoes: pd.DataFrame):
        self.cotacoes = cotacoes
        self.indicadores: Iterable[str] = cotacoes["codigo"].unique()

    @staticmethod
    def _instanciar_indicador(nome_indicador: str) -> IndicadorAbstrato:
        mapa_classes = {
            "IMAB 5": IMAB5,
            "VNA": VNA,
            "CDI": CDI,
        }

        classe_indicador = mapa_classes.get(nome_indicador, TickerBolsa)
        if classe_indicador in [IMAB5, VNA, CDI]:
            return classe_indicador()
        elif nome_indicador == "IBOV":
            return classe_indicador("^BVSP")
        else:
            return classe_indicador(nome_indicador + ".SA")

    def _criar_df_novas_cotacoes(
        self, nome_indicador: str, datas_faltantes: pd.Series, variacao: bool = False
    ) -> pd.DataFrame:
        indicador = self._instanciar_indicador(nome_indicador)
        valores = [indicador.extrair(data) for data in datas_faltantes]

        df_layout = {
            "data": datas_faltantes,
            "codigo": nome_indicador,
        }
        if variacao:
            df_layout["valor"] = np.nan
            df_layout["variacao"] = valores
        else:
            df_layout["valor"] = valores
            df_layout["variacao"] = np.nan

        return pd.DataFrame(df_layout)

    def _calcular_variacoes_faltantes(self):
        variacoes = self.cotacoes.groupby("codigo")["valor"].pct_change(fill_method=None) + 1
        linhas_sem_variacao = (
            self.cotacoes["valor"].notnull() & self.cotacoes["variacao"].isnull()
        )
        self.cotacoes.loc[linhas_sem_variacao, "variacao"] = variacoes[
            linhas_sem_variacao
        ]

    def atualizar_indicadores(self, dias: int = 180):
        """Verifica se há cotações faltantes dentro de um período de tempo (padrão 60 dias).
        Se sim, serão extraídas e adicionadas ao dataframe.
        """

        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=dias)
        dias_uteis: pd.Series = calcular_dias_uteis_entre(data_inicio, data_fim)
        linhas_periodo = self.cotacoes[self.cotacoes["data"].ge(dias_uteis.iloc[0])]

        for nome_indicador in self.indicadores:
            # Filtrando datas faltantes para o indicador
            datas_cotacoes = linhas_periodo.loc[
                linhas_periodo["codigo"].eq(nome_indicador), "data"
            ]
            datas_faltantes = dias_uteis[~dias_uteis.isin(datas_cotacoes)]

            if datas_faltantes.empty:
                print(f"Não há dados faltantes em {nome_indicador}")
                continue

            novas_cotacoes = self._criar_df_novas_cotacoes(
                nome_indicador,
                datas_faltantes,
                True if nome_indicador == "CDI" else False,
            )

            self.cotacoes = pd.concat([self.cotacoes, novas_cotacoes]).sort_values(
                ["codigo", "data"]
            )

        self._calcular_variacoes_faltantes()

    def salvar_cotacoes(self):
        self.cotacoes.to_parquet("data/cotacoes.parquet", index=False)


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
