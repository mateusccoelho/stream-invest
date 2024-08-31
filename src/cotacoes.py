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

        novas_cotacoes = pd.DataFrame(df_layout)
        if not variacao:
            novas_cotacoes = novas_cotacoes.loc[novas_cotacoes["valor"].notnull(), :]
        return novas_cotacoes

    def _calcular_variacoes_faltantes(self):
        variacoes = (
            self.cotacoes.groupby("codigo")["valor"].pct_change(fill_method=None) + 1
        )
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

            if not novas_cotacoes.empty:
                self.cotacoes = pd.concat([self.cotacoes, novas_cotacoes]).sort_values(
                    ["codigo", "data"]
                )
            else:
                print(
                    f"{nome_indicador} tem dados faltantes mas não é possível preenchê-los"
                )

        self._calcular_variacoes_faltantes()

    def salvar_cotacoes(self):
        self.cotacoes.to_parquet("dados/cotacoes.parquet", index=False)
