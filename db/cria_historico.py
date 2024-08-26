import sys
sys.path.append("..")
from datetime import date

import pandas as pd

from db.atualizar_indicadores import extract_ticker
from db.operacoes_renda_fixa import adiciona_titulo_rf, adiciona_resgate_rf
from db.operacoes_renda_variavel import (
    adiciona_provento,
    adiciona_ativo,
    adiciona_transacoes,
)
from db.definicao_tabelas import Session, Cotacoes


def cria_historico_cotacoes():
    with Session() as session:
        ativos = pd.read_excel(
            "../Investimentos.xlsx", sheet_name="Ativos RV", engine="openpyxl"
        )
        codigos = ativos["Código"].unique()

        for codigo in codigos:
            df = extract_ticker(codigo, date(2024, 1, 1))
            for data, close, variacao in zip(df["Date"], df["Close"], df["Variacao"]):
                cotacao = Cotacoes(
                    data=data, codigo=codigo, valor=close, variacao=variacao
                )
                session.add(cotacao)

        session.commit()


def cria_historico_transacoes():
    df = pd.read_excel(
        "../Investimentos.xlsx", sheet_name="Transações RV", engine="openpyxl"
    )
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date

    gb = df.groupby(["Data", "Código", "Operação C/V", "Corretora"])
    for (data, codigo, tipo, corretora), idxs in gb.groups.items():
        adiciona_transacoes(
            data=data,
            codigo=codigo,
            tipo=tipo,
            corretora=corretora,
            quantidades=df.loc[idxs, "Quantidade"].tolist(),
            precos=df.loc[idxs, "Preço"].tolist(),
            taxas=df.loc[idxs, "Taxas"].tolist(),
        )


def adiciona_historico_ativos():
    df = pd.read_excel(
        "../Investimentos.xlsx", sheet_name="Ativos RV", engine="openpyxl"
    )

    for _, row in df.iterrows():
        adiciona_ativo(
            codigo=row["Código"],
            tipo=row["Tipo"],
            benchmark=row["Benchmark"],
        )


def criar_historico_indicadores():
    df = pd.read_excel(
        "../Investimentos.xlsx",
        sheet_name="Indicadores",
        engine="openpyxl",
    )
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date
    df = df.set_index("Data").dropna(how="all")

    with Session() as session:
        for index, row in df.iterrows():
            for codigo in ["VNA", "IBOV", "IMAB 5"]:
                if pd.isnull(row[codigo]):
                    continue

                cotacao = Cotacoes(
                    data=index,
                    codigo=codigo,
                    valor=row[codigo],
                    variacao=row[f"Fator {codigo}"],
                )
                session.add(cotacao)

            cotacao = Cotacoes(
                data=index,
                codigo="CDI",
                variacao=row["CDI"],
            )
            session.add(cotacao)

        session.commit()


def criar_historico_aportes_rf():
    df = pd.read_excel(
        "../Investimentos.xlsx",
        sheet_name="Aportes RF",
        engine="openpyxl",
    )

    for col in ["Data compra", "Data vencimento"]:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y").dt.date

    for _, row in df.iterrows():
        adiciona_titulo_rf(
            corretora=row["Corretora"],
            emissor=row["Emissor"],
            tipo=row["Tipo"],
            forma=row["Forma"],
            indexador=row["Indexador"],
            data_compra=row["Data compra"],
            data_vencimento=row["Data vencimento"],
            taxa=row["Taxa"],
            valor=row["Valor"],
        )


def cria_historico_resgates():
    df = pd.read_excel(
        "../Investimentos.xlsx",
        sheet_name="Resgates RF",
        engine="openpyxl",
    )

    for col in ["Data resgate"]:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y").dt.date

    for _, resgate_row in df.iterrows():
        adiciona_resgate_rf(
            id_titulo=resgate_row["ID"],
            data_resgate=resgate_row["Data resgate"],
            valor_resgate=resgate_row["Valor"],
        )


def adiciona_historico_proventos():
    df = pd.read_excel(
        "../Investimentos.xlsx", sheet_name="Proventos RV", engine="openpyxl"
    )
    df["Data pagamento"] = pd.to_datetime(df["Data pagamento"], format="%d/%m/%Y")

    for _, row in df.iterrows():
        adiciona_provento(
            data=row["Data pagamento"],
            codigo=row["Código"],
            valor=row["Valor"],
            quantidade=row["Quantidade"],
            tipo=row["Tipo"],
        )


if __name__ == "__main__":
    adiciona_historico_proventos()
    # adiciona_historico_ativos()
    # cria_historico_transacoes()
    pass
