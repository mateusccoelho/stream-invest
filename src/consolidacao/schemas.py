"""Schemas Pandera para os DataFrames produzidos no pacote de consolidação."""

import datetime

import pandera.pandas as pa


_data_check = pa.Check(
    lambda s: s.apply(lambda x: isinstance(x, datetime.date)),
    element_wise=False,
    error="Coluna deve conter objetos datetime.date",
)

ProventosTratadosSchema = pa.DataFrameSchema(
    columns={
        "total": pa.Column(float, checks=pa.Check.gt(0)),
        "anomes": pa.Column(object, checks=_data_check),
    },
    name="proventos_tratados",
    strict="filter",
)

PatrimonioRFSchema = pa.DataFrameSchema(
    columns={
        "data": pa.Column(object, checks=_data_check),
        "valor": pa.Column(float, checks=pa.Check.gt(0)),
        "rendimento": pa.Column(float),
        "taxa": pa.Column(float),
        "id": pa.Column(int, checks=pa.Check.ge(1), nullable=False),
    },
    name="patrimonio_rf",
    unique=["data", "id"],
)

CarteiraRFSchema = pa.DataFrameSchema(
    columns={
        "id": pa.Column(int, checks=pa.Check.ge(1), nullable=False),
        "data_atualizacao": pa.Column(object, checks=_data_check),
        "saldo": pa.Column(float, checks=pa.Check.ge(0)),
        "resgates": pa.Column(float, checks=pa.Check.ge(0)),
        "rendimentos_bruto": pa.Column(float),
        "status": pa.Column(int, checks=pa.Check.isin([0, 1])),
    },
    name="carteira_rf",
    unique=["id"],
)

PatrimonioRVSchema = pa.DataFrameSchema(
    columns={
        "data": pa.Column(object, checks=_data_check),
        "codigo": pa.Column(str),
        "qtd": pa.Column(float, checks=pa.Check.ge(0)),
        "preco_medio": pa.Column(float, checks=pa.Check.ge(0)),
        "patrimonio": pa.Column(float, checks=pa.Check.ge(0)),
    },
    name="patrimonio_rv",
    unique=["data", "codigo"],
)

CarteiraRVSchema = pa.DataFrameSchema(
    columns={
        "data": pa.Column(object, checks=_data_check),
        "qtd": pa.Column(float, checks=pa.Check.ge(0)),
        "preco_medio": pa.Column(float, checks=pa.Check.ge(0)),
        "patrimonio": pa.Column(float, checks=pa.Check.ge(0)),
        "status": pa.Column(int, checks=pa.Check.isin([0, 1])),
        "rendimento_total": pa.Column(float),
    },
    index=pa.Index(str, name="codigo"),
    name="carteira_rv",
)
