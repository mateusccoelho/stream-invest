import sys

sys.path.append("..")
from datetime import date

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session as SessionType

from definicao_tabelas import (
    Session,
    Cotacoes,
    AportesRendaFixa,
    CarteiraRF,
    PatrimonioRF,
    ResgatesRF,
)
from utils.calendario import dia_util_anterior, dias_uteis_no_intervalo


def obter_serie_variacao(
    data_inicio: date, data_fim: date, codigo: str
) -> pd.DataFrame:
    with Session() as session:
        cotacoes = (
            session.query(Cotacoes.data, Cotacoes.variacao)
            .filter(
                Cotacoes.codigo == codigo,
                Cotacoes.data >= data_inicio,
                Cotacoes.data <= data_fim,
            )
            .order_by(Cotacoes.data)
            .all()
        )
        cotacoes = pd.DataFrame(cotacoes, columns=["data", "variacao"]).set_index(
            "data"
        )["variacao"]
        return cotacoes


def calcula_valor_titulo_periodo(
    tipo_rentabilidade: str,
    data_inicio: date,
    data_fim: date,
    taxa: float,
    valor: float,
) -> pd.DataFrame:
    if tipo_rentabilidade == "CDI":
        valores_indicador = obter_serie_variacao(data_inicio, data_fim, "CDI")
        fator_diario = valores_indicador * taxa + 1
    elif tipo_rentabilidade == "Pré":
        dias_uteis = dias_uteis_no_intervalo(data_inicio, data_fim)
        fator_diario = pd.Series((taxa + 1) ** (1 / 252), index=dias_uteis)
    elif tipo_rentabilidade == "IPCA +":
        valores_indicador = obter_serie_variacao(data_inicio, data_fim, "VNA")
        fator_diario = valores_indicador * ((taxa + 1) ** (1 / 252))

    patrimonio = fator_diario.cumprod() * valor
    rendimento = patrimonio - patrimonio.shift(1).fillna(valor)
    return pd.concat(
        [patrimonio, rendimento, fator_diario],
        axis=1,
        keys=["valor", "rendimento", "taxa"],
    )


def adiciona_titulo_rf(
    corretora: str,
    emissor: str,
    tipo: str,
    forma: str,
    indexador: str,
    data_compra: date,
    data_vencimento: date,
    taxa: float,
    valor: float,
):
    with Session() as session:
        aporte = AportesRendaFixa(
            corretora=corretora,
            emissor=emissor,
            tipo=tipo,
            forma=forma,
            indexador=indexador,
            data_compra=data_compra,
            data_vencimento=data_vencimento,
            taxa=taxa,
            valor_aplicado=valor,
        )
        session.add(aporte)
        session.flush()
        session.refresh(aporte)
        id_titulo = aporte.id_titulo

        valor_titulo = calcula_valor_titulo_periodo(
            tipo_rentabilidade=indexador,
            data_inicio=data_compra,
            data_fim=data_vencimento,
            taxa=taxa,
            valor=valor,
        )

        for index, row in valor_titulo.iterrows():
            patrimonio = PatrimonioRF(
                data=index,
                id_titulo=id_titulo,
                valor=row["valor"],
                rendimento=row["rendimento"],
                taxa=row["taxa"],
            )
            session.add(patrimonio)

        carteira = CarteiraRF(
            id_titulo=id_titulo,
            data_atualizacao=valor_titulo.index[-1],
            saldo=valor_titulo["valor"].iloc[-1],
            resgates=0,
            rendimentos_bruto=valor_titulo["rendimento"].sum(),
            status=1,
        )
        session.add(carteira)

        session.commit()


def adiciona_resgate_rf(
    id_titulo: int,
    data_resgate: date,
    valor_resgate: float,
):
    with Session() as session:
        resgate = ResgatesRF(
            id_titulo=id_titulo,
            data=data_resgate,
            valor=valor_resgate,
        )
        session.add(resgate)

        # Tanto em caso de resgate parcial ou total os valor após resgate precisam
        # ser deletados.
        session.query(PatrimonioRF).filter(
            PatrimonioRF.id_titulo == id_titulo,
            PatrimonioRF.data >= data_resgate,
        ).delete()

        carteira_titulo = session.get(CarteiraRF, id_titulo)

        # Valida se o resgate foi total ou parcial baseado no saldo restante.
        dia_anterior = dia_util_anterior(data_resgate)
        saldo_anterior = (
            session.query(PatrimonioRF.valor)
            .filter(
                PatrimonioRF.id_titulo == id_titulo,
                PatrimonioRF.data == dia_anterior,
            )
            .scalar()
        )
        if not saldo_anterior:
            print("Erro ao cadastrar resgate. Saldo do dia anterior não encontrado.")
            return

        saldo_restante = saldo_anterior - valor_resgate

        if saldo_restante < 0.01:
            print("Título encerrado, resgate total.")

            session.query(CarteiraRF).filter(
                CarteiraRF.id_titulo == id_titulo,
            ).update(
                {
                    "data_atualizacao": data_resgate,
                    "saldo": 0,
                    "resgates": carteira_titulo.resgates + valor_resgate,
                    "rendimentos_bruto": carteira_titulo.rendimentos_bruto,
                    "status": 0,
                }
            )
        else:
            print("Resgate parcial.")

            # Os valores após resgate precisam ser recalculados pois o valor base
            # mudou.
            titulo_info = (
                session.query(AportesRendaFixa)
                .filter(
                    AportesRendaFixa.id_titulo == id_titulo,
                )
                .one()
            )
            novos_valores = calcula_valor_titulo_periodo(
                tipo_rentabilidade=titulo_info.indexador,
                data_inicio=data_resgate,
                data_fim=titulo_info.data_vencimento,
                taxa=titulo_info.taxa,
                valor=saldo_restante,
            )

            for index, patr_row in novos_valores.iterrows():
                patrimonio = PatrimonioRF(
                    data=index,
                    id_titulo=id_titulo,
                    valor=patr_row["valor"],
                    rendimento=patr_row["rendimento"],
                    taxa=patr_row["taxa"],
                )
                session.add(patrimonio)

            rendimento_antes_do_resgate = (
                session.query(func.sum(PatrimonioRF.rendimento))
                .filter(
                    PatrimonioRF.id_titulo == id_titulo,
                    PatrimonioRF.data < data_resgate,
                )
                .scalar()
            )

            session.query(CarteiraRF).filter(
                CarteiraRF.id_titulo == id_titulo,
            ).update(
                {
                    "data_atualizacao": novos_valores.index[-1],
                    "saldo": novos_valores["valor"].iloc[-1],
                    "resgates": carteira_titulo.resgates + valor_resgate,
                    "rendimentos_bruto": rendimento_antes_do_resgate
                    + novos_valores["rendimento"].sum(),
                    "status": 1,
                }
            )

        session.commit()


def remove_titulo(id_titulo: int):
    with Session() as session:
        session.query(AportesRendaFixa).filter(
            AportesRendaFixa.id_titulo == id_titulo,
        ).delete()
        session.query(CarteiraRF).filter(
            CarteiraRF.id_titulo == id_titulo,
        ).delete()
        session.query(PatrimonioRF).filter(
            PatrimonioRF.id_titulo == id_titulo,
        ).delete()
        session.query(ResgatesRF).filter(
            ResgatesRF.id_titulo == id_titulo,
        ).delete()
        session.commit()


def atualizar_titulos():
    with Session() as session:
        data_max = (
            session.query(
                Cotacoes.codigo,
                func.max(Cotacoes.data),
            )
            .filter(Cotacoes.codigo.in_(["VNA", "CDI"]))
            .group_by(Cotacoes.codigo)
            .all()
        )
        data_max = dict(data_max)

        carteira_info = session.query(CarteiraRF, AportesRendaFixa).filter(
            CarteiraRF.id_titulo == AportesRendaFixa.id_titulo,
            CarteiraRF.status == 1,
        )

        for row in carteira_info:
            id_titulo = row.CarteiraRF.id_titulo
            data_atualizacao = row.CarteiraRF.data_atualizacao
            tipo_rentabilidade = row.AportesRendaFixa.indexador
            data_vencimento = row.AportesRendaFixa.data_vencimento

            if data_atualizacao >= data_max["VNA"]:
                continue

            novo_valor = calcula_valor_titulo_periodo(
                # tipo_rentabilidade=,
                data_inicio=data_atualizacao,
                data_fim=data_vencimento,
                taxa=row.AportesRendaFixa.taxa,
                valor=row.CarteiraRF.saldo,
            )

            for index, patr_row in novo_valor.iterrows():
                patrimonio = PatrimonioRF(
                    data=index,
                    id_titulo=id_titulo,
                    valor=patr_row["valor"],
                    rendimento=patr_row["rendimento"],
                    taxa=patr_row["taxa"],
                )
                session.add(patrimonio)

            rendimento_antes_do_resgate = (
                session.query(func.sum(PatrimonioRF.rendimento))
                .filter(
                    PatrimonioRF.id_titulo == id_titulo,
                    PatrimonioRF.data < data_vencimento,
                )
                .scalar()
            )

            session.query(CarteiraRF).filter(
                CarteiraRF.id_titulo == id_titulo,
            ).update(
                {
                    "data_atualizacao": novo_valor.index[-1],
                    "saldo": novo_valor["valor"].iloc[-1],
                    "rendimentos_bruto": rendimento_antes_do_resgate
                    + novo_valor["rendimento"].sum(),
                }
            )
