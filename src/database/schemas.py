"""
Schemas Pandera para os DataFrames retornados pelas funções de leitura
do módulo database.py.
"""

import datetime

import pandera.pandas as pa

_data_check = pa.Check(
    lambda s: s.apply(lambda x: isinstance(x, datetime.date)),
    element_wise=False,
    error="Coluna deve conter objetos datetime.date",
)

AportesRFSchema = pa.DataFrameSchema(
    columns={
        "id": pa.Column(int, nullable=False),
        "corretora": pa.Column(str),
        "emissor": pa.Column(str),
        "tipo": pa.Column(str),
        "forma": pa.Column(str),
        "data_compra": pa.Column(object, checks=_data_check),
        "data_venc": pa.Column(object, checks=_data_check),
        "index": pa.Column(str),
        "taxa": pa.Column(float),
        "valor": pa.Column(float, checks=pa.Check.gt(0)),
        "reserva": pa.Column(bool),
    },
    name="aportes_rf",
)

ResgatesRFSchema = pa.DataFrameSchema(
    columns={
        "id": pa.Column(int, nullable=False),
        "data_resgate": pa.Column(object, checks=_data_check),
        "valor": pa.Column(float, checks=pa.Check.gt(0)),
        "final": pa.Column(bool),
    },
    name="resgates_rf",
)

TransacoesRVSchema = pa.DataFrameSchema(
    columns={
        "data": pa.Column(object, checks=_data_check),
        "codigo": pa.Column(str),
        "tipo": pa.Column(
            str,
            checks=pa.Check.isin(["C", "V"]),
        ),
        "qtd": pa.Column(int, checks=pa.Check.gt(0)),
        "preco": pa.Column(float, checks=pa.Check.gt(0)),
        "corretora": pa.Column(str),
        "taxas": pa.Column(float, checks=pa.Check.ge(0)),
    },
    name="transacoes_rv",
)

ProventosRVSchema = pa.DataFrameSchema(
    columns={
        "dt_pag": pa.Column(object, checks=_data_check),
        "codigo": pa.Column(str),
        "qtd": pa.Column(int, checks=pa.Check.gt(0)),
        "valor": pa.Column(float, checks=pa.Check.gt(0)),
        "tipo": pa.Column(str),
    },
    name="proventos_rv",
)

AtivosRVSchema = pa.DataFrameSchema(
    columns={
        "codigo": pa.Column(str),
        "tipo_ativo": pa.Column(str),
        "bench": pa.Column(str),
    },
    name="ativos_rv",
)

ProporcoesSchema = pa.DataFrameSchema(
    columns={
        "classe": pa.Column(str),
        "proporcao": pa.Column(
            float,
            checks=pa.Check.in_range(0.0, 1.0),
        ),
    },
    name="proporcoes",
)

CotacoesSchema = pa.DataFrameSchema(
    columns={
        "data": pa.Column(object, checks=_data_check),
        "codigo": pa.Column(str),
        "valor": pa.Column(float, nullable=True),
        "variacao": pa.Column(float, nullable=True),
    },
    name="cotacoes",
)

PagamentosIRSchema = pa.DataFrameSchema(
    columns={
        "data_pagamento": pa.Column(object, checks=_data_check),
        "ano_ref": pa.Column(int),
        "mes_ref": pa.Column(int, checks=pa.Check.in_range(1, 12)),
        "valor": pa.Column(float, checks=pa.Check.gt(0)),
    },
    name="pagamentos_ir",
)
