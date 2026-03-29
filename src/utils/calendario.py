from typing import List
from datetime import date
from pathlib import Path

import pandas as pd

CAMINHO_DADOS = Path(__file__).resolve().parent.parent.parent / "dados"


def le_feriados() -> pd.DatetimeIndex:
    csv_path = str(CAMINHO_DADOS / "feriados.csv")
    feriados = pd.read_csv(csv_path, header=None, skiprows=200, nrows=200)[0].tolist()
    feriados = pd.to_datetime(feriados, format="%d/%m/%Y")
    return feriados


def eh_dia_util(data: pd.Timestamp, feriados: pd.DatetimeIndex) -> bool:
    return data.weekday() < 5 and data not in feriados


def dias_uteis_no_intervalo(data_inicial: date, data_final: date) -> List[date]:
    feriados = le_feriados()
    dias_uteis = pd.date_range(start=data_inicial, end=data_final, freq="B")
    return [dia.date() for dia in dias_uteis if eh_dia_util(dia, feriados)]
