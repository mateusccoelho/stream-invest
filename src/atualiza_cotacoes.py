from datetime import date, timedelta

import pandas as pd

from utils.calendario import dias_uteis_no_intervalo
from indicadores import IMAB5, VNA, TickerBolsa, CDI
from database import ler_datas_cotacoes, inserir_cotacao


indicadores = {
    "ACWI11": TickerBolsa("ACWI11.SA"),
    "B5P211": TickerBolsa("B5P211.SA"), 
    "BDIF11": TickerBolsa("BDIF11.SA"), 
    "CDI": CDI(),
    "CDII11": TickerBolsa("CDII11.SA"), 
    "IBOV": TickerBolsa("^BVSP"), 
    "IMAB 5": IMAB5(), 
    "JURO11": TickerBolsa("JURO11.SA"), 
    "PIBB11": TickerBolsa("PIBB11.SA"), 
    "VNA": VNA()
}


def atualizar_indicadores(dias: int = 180):
    """Verifica se há cotações faltantes dentro de um período de tempo (padrão 180 dias). Se sim, serão extraídas e inseridas diretamente no banco."""

    data_fim = date.today()
    data_inicio = data_fim - timedelta(days=dias)
    dias_uteis = dias_uteis_no_intervalo(data_inicio, data_fim)

    for nome_indicador in indicadores:
        datas_existentes = ler_datas_cotacoes(
            nome_indicador, dias_uteis[0]
        )
        datas_faltantes = [dia for dia in dias_uteis if dia not in datas_existentes]

        if not datas_faltantes:
            print(f"Não há dados faltantes em {nome_indicador}")
            continue

        indicador = indicadores[nome_indicador]
        valores = [indicador.extrair(data) for data in datas_faltantes]

        count = 0
        for data, valor in zip(datas_faltantes, valores):
            if nome_indicador == "CDI":
                inserir_cotacao(
                    data=str(data),
                    codigo=nome_indicador,
                    valor=None,
                    variacao=valor,
                )
                count += 1
            else:
                if valor is not None:
                    inserir_cotacao(
                        data=str(data),
                        codigo=nome_indicador,
                        valor=valor,
                        variacao=None,
                    )
                    count += 1

        if count > 0:
            print(f"{nome_indicador}: {count} cotações inseridas.")
        else:
            print(
                f"{nome_indicador} tem dados faltantes mas não é possível preenchê-los."
            )
            print(f"Datas faltantes: {', '.join(str(d) for d in datas_faltantes)}")


if __name__ == "__main__":
    atualizar_indicadores()
