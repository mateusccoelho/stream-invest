from typing import List
from datetime import date
from pathlib import Path

import pandas as pd

FILE_PATH = Path(__file__).resolve().parent.parent.parent / "dados"


def le_feriados() -> List[pd.Timestamp]:
    csv_path = str(FILE_PATH / "feriados.csv")
    feriados = pd.read_csv(csv_path, header=None)[0].tolist()
    feriados = pd.to_datetime(feriados, format="%d/%m/%Y")
    return feriados


def le_dias_uteis() -> List[pd.Timestamp]:
    csv_path = str(FILE_PATH / "dias_uteis.csv")
    dias_uteis = pd.read_csv(csv_path, header=None, parse_dates=[0]).squeeze("columns").dt.date
    return dias_uteis


def le_dias_sem_pregao() -> List[pd.Timestamp]:
    csv_path = str(FILE_PATH / "dias_sem_pregao.csv")
    dias_sem_pregao = pd.read_csv(csv_path, header=None, parse_dates=[0]).squeeze("columns").dt.date
    return dias_sem_pregao


def eh_dia_util(data: pd.Timestamp, feriados: List[pd.Timestamp]) -> bool:
    return data.weekday() < 5 and data not in feriados


def dias_uteis_no_intervalo(data_inicial: date, data_final: date) -> List[date]:
    feriados = le_feriados()
    dias_uteis = pd.date_range(start=data_inicial, end=data_final, freq="B")
    return [dia.date() for dia in dias_uteis if eh_dia_util(dia, feriados)]


def gerar_csv_dias_uteis():
    dias_uteis = dias_uteis_no_intervalo(date(2020, 1, 1), date(2030, 12, 31))
    df = pd.DataFrame(dias_uteis, columns=["Data"])
    df.to_csv(str(FILE_PATH / "dias_uteis.csv"), index=False, header=False)


def dia_util_anterior(data: date, considerar_pregao=False) -> pd.Timestamp:
    dias_uteis = le_dias_uteis()
    if considerar_pregao:
        dias_sem_pregao = le_dias_sem_pregao()
        dias_uteis = dias_uteis[~dias_uteis.isin(dias_sem_pregao)]
        dias_uteis = dias_uteis.reset_index(drop=True)

    idx = dias_uteis[dias_uteis == data].index[0]
    return dias_uteis[idx - 1]


if __name__ == "__main__":
    gerar_csv_dias_uteis()