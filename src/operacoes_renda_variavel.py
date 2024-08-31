from datetime import date
from typing import List
import sys
sys.path.append("..")

import pandas as pd

from utils.calendario import dias_uteis_no_intervalo, dia_util_anterior


def calcula_patrimonio_rv(
    session: SessionType,
    codigo: str,
    data_inicio: date,
    quantidade: int,
    patrimonio_anterior: float,
    valor_transacionado: float,
    tipo_operacao: str,
) -> pd.Series:
    dias = dias_uteis_no_intervalo(data_inicial=data_inicio, data_final=date.today())
    dias = pd.DataFrame(dias, columns=["dia_util"])

    cotacoes = (
        session.query(Cotacoes.data, Cotacoes.valor)
        .filter(
            Cotacoes.codigo == codigo,
            Cotacoes.data >= data_inicio,
            Cotacoes.data <= date.today(),
        )
        .all()
    )
    cotacoes = pd.DataFrame(cotacoes)

    patrimonio = (
        dias.merge(cotacoes, left_on="dia_util", right_on="data", how="left")
        .drop(columns="data")
        .set_index("dia_util")
        .ffill()
    )
    patrimonio["patrimonio"] = patrimonio["valor"] * quantidade
    patrimonio["rendimento"] = patrimonio["patrimonio"] - patrimonio[
        "patrimonio"
    ].shift(1)

    if tipo_operacao == "C":
        valor_base = patrimonio_anterior + valor_transacionado
    else:
        valor_base = patrimonio_anterior - valor_transacionado

    patrimonio.loc[patrimonio.index[0], "rendimento"] = (
        patrimonio.loc[patrimonio.index[0], "patrimonio"] - valor_base
    )
    return patrimonio


def adiciona_transacoes(
    data: date,
    codigo: str,
    tipo: str,
    corretora: str,
    quantidades: List[int],
    precos: List[float],
    taxas: List[float],
):
    with Session() as session:
        valor_transacionado = 0
        for quantidade, preco, taxa in zip(quantidades, precos, taxas):
            transacao = TransacoesRV(
                data=data,
                codigo=codigo,
                quantidade=quantidade,
                preco=preco,
                tipo=tipo,
                corretora=corretora,
                taxa=taxa,
            )
            session.add(transacao)
            valor_transacionado += quantidade * preco + taxa

        patr_anterior = session.get(
            PatrimonioRV, {"codigo": codigo, "data": dia_util_anterior(data)}
        )
        ativo_info = session.query(CarteiraRV).filter(CarteiraRV.codigo == codigo)
        if patr_anterior:
            session.query(PatrimonioRV).filter(
                PatrimonioRV.codigo == codigo, PatrimonioRV.data >= data
            ).delete()

            if tipo == "C":
                quantidade_nova = patr_anterior.quantidade + sum(quantidades)
                preco_medio_novo = (
                    patr_anterior.quantidade * patr_anterior.preco_medio
                    + valor_transacionado
                ) / quantidade_nova
            else:
                quantidade_nova = patr_anterior.quantidade - sum(quantidades)
                preco_medio_novo = patr_anterior.preco_medio
                if quantidade_nova <= 0:
                    ativo_info.update(
                        {
                            "data_atualizacao": data,
                            "quantidade": 0,
                            "patrimonio": 0,
                            "rendimento_hoje": 0,
                            "rendimento_total": 0,
                            "status": 0,
                        }
                    )
                    session.commit()
                    return
        else:
            quantidade_nova = sum(quantidades)
            preco_medio_novo = valor_transacionado / quantidade_nova

        patrimonio_novo = calcula_patrimonio_rv(
            session=session,
            codigo=codigo,
            data_inicio=data,
            quantidade=quantidade_nova,
            valor_transacionado=(
                valor_transacionado
                if tipo == "C"
                else preco_medio_novo * sum(quantidades)
            ),
            tipo_operacao=tipo,
            patrimonio_anterior=patr_anterior.patrimonio if patr_anterior else 0,
        )

        for dia, linha in patrimonio_novo.iterrows():
            novo_patrimonio = PatrimonioRV(
                data=dia,
                codigo=codigo,
                quantidade=quantidade_nova,
                preco_medio=preco_medio_novo,
                patrimonio=linha["patrimonio"],
                rendimento=linha["rendimento"],
            )
            session.add(novo_patrimonio)

        if patr_anterior:
            ativo_info.update(
                {
                    "data_atualizacao": patrimonio_novo.index[-1],
                    "quantidade": quantidade_nova,
                    "patrimonio": patrimonio_novo["patrimonio"].iloc[-1],
                    "preco_medio": preco_medio_novo,
                    "rendimento_hoje": patrimonio_novo["rendimento"].iloc[-1],
                    "rendimento_total": patrimonio_novo["patrimonio"].iloc[-1]
                    - preco_medio_novo * quantidade_nova,
                }
            )
        else:
            ativo_info = CarteiraRV(
                codigo=codigo,
                data_atualizacao=patrimonio_novo.index[-1],
                quantidade=quantidade_nova,
                patrimonio=patrimonio_novo["patrimonio"].iloc[-1],
                preco_medio=preco_medio_novo,
                rendimento_hoje=patrimonio_novo["rendimento"].iloc[-1],
                rendimento_total=patrimonio_novo["patrimonio"].iloc[-1]
                - preco_medio_novo * quantidade_nova,
                status=1,
            )
            session.add(ativo_info)

        session.commit()
