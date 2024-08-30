import pandas as pd


def le_dados_excel(sheet: str = None) -> pd.DataFrame | dict[str, pd.DataFrame]:
    return pd.read_excel(
        "dados/Investimentos.xlsx", sheet_name=sheet, engine="openpyxl"
    )


def le_dados_indicadores() -> pd.DataFrame:
    return pd.read_excel(
        "dados/Investimentos - Restos.xlsx",
        sheet_name="Indicadores",
        engine="openpyxl",
    )
