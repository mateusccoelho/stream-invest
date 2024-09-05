from datetime import date

import pandas as pd

from utils.calendario import dia_util_anterior, dias_uteis_no_intervalo


def consolidar_renda_fixa(
    aportes: pd.DataFrame, resgates: pd.DataFrame, cotacoes: pd.DataFrame
) -> pd.DataFrame:
    patrimonio_rf = []
    status = {"id": [], "status": []}

    for id_titulo in aportes["id"].unique():
        aporte = aportes.loc[aportes["id"].eq(id_titulo)].iloc[0]
        resgates_titulo = (
            resgates.loc[resgates["id"].eq(id_titulo)]
            .sort_values("data_resgate")
        )
        
        valor_titulo = calcula_valor_titulo_periodo(
            cotacoes,
            tipo_rentabilidade=aporte["index"],
            data_inicio=aporte["data_compra"],
            data_fim=aporte["data_venc"],
            taxa=aporte["taxa"],
            valor=aporte["valor"],
        )
        valor_titulo["id"] = aporte["id"]

        for _, row in resgates_titulo.iterrows():
            valor_titulo = valor_titulo.loc[
                valor_titulo["data"].lt(row["data_resgate"]), :
            ]
            ultimo_saldo = valor_titulo.iloc[-1, :]["valor"]
            saldo_restante = ultimo_saldo - row["valor"]

            if saldo_restante >= 0.01:
                novos_valores = calcula_valor_titulo_periodo(
                    cotacoes,
                    tipo_rentabilidade=aporte["index"],
                    data_inicio=row["data_resgate"],
                    data_fim=aporte["data_venc"],
                    taxa=aporte["taxa"],
                    valor=saldo_restante,
                )
                novos_valores["id"] = aporte["id"]
                
                valor_titulo = pd.concat([valor_titulo, novos_valores])
            else:
                status["id"].append(aporte["id"])
                status["status"].append(0)

        patrimonio_rf.append(valor_titulo)
        
    patrimonio_rf = pd.concat(patrimonio_rf, ignore_index=True)

    carteira_rf = patrimonio_rf.groupby("id", as_index=False).agg(
        data_atualizacao=pd.NamedAgg(column="data", aggfunc="max"),
        saldo=pd.NamedAgg(column="valor", aggfunc="last"),
        rendimentos_bruto=pd.NamedAgg(column="rendimento", aggfunc="sum"),
    )
    resgates.groupby("id", as_index=False).agg(
        resgates=pd.NamedAgg(column="valor", aggfunc="sum")
    )


def obter_serie_variacao(
    cotacoes: pd.DataFrame, data_inicio: date, data_fim: date, codigo: str
) -> pd.Series:
    mascara_datas = cotacoes["data"].ge(data_inicio) & cotacoes["data"].le(data_fim)
    mascara_codigo = cotacoes["codigo"].eq(codigo)
    df = cotacoes.loc[mascara_datas & mascara_codigo, ["data", "variacao"]]
    return df.set_index("data")["variacao"]


def calcula_valor_titulo_periodo(
    cotacoes: pd.DataFrame,
    tipo_rentabilidade: str,
    data_inicio: date,
    data_fim: date,
    taxa: float,
    valor: float,
) -> pd.DataFrame:
    if tipo_rentabilidade == "CDI":
        valores_indicador = obter_serie_variacao(cotacoes, data_inicio, data_fim, "CDI")
        fator_diario = valores_indicador * taxa + 1
    elif tipo_rentabilidade == "Pré":
        data_fim = data_fim if data_fim <= date.today() else date.today()
        dias_uteis = dias_uteis_no_intervalo(data_inicio, data_fim)
        fator_diario = pd.Series((taxa + 1) ** (1 / 252), index=dias_uteis, name="variacao")
        fator_diario.index.name = "data"
    elif tipo_rentabilidade == "IPCA +":
        valores_indicador = obter_serie_variacao(cotacoes, data_inicio, data_fim, "VNA")
        fator_diario = valores_indicador * ((taxa + 1) ** (1 / 252))

    patrimonio = fator_diario.cumprod() * valor
    rendimento = patrimonio - patrimonio.shift(1).fillna(valor)
    return pd.concat(
        [patrimonio, rendimento, fator_diario],
        axis=1,
        keys=["valor", "rendimento", "taxa"],
    ).reset_index()


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

