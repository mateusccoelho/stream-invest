from datetime import date

import pandas as pd

from src.utils.calendario import dias_uteis_no_intervalo


def consolidar_renda_fixa(
    aportes: pd.DataFrame, resgates: pd.DataFrame, cotacoes: pd.DataFrame
) -> pd.DataFrame:
    """O caso em que o valor calculado aqui e o valor devolvido real não batem deve
    ser tratado. Pode-se adicionar um resgate com o valor real e criar uma coluna para
    indicar os resgates finais."""

    patrimonio_rf = []
    carteira_rf = {
        "id": [],
        "data_atualizacao": [],
        "saldo": [],
        "resgates": [],
        "rendimentos_bruto": [],
        "status": [],
    }

    for id_titulo in aportes["id"].unique():
        aporte = aportes.loc[aportes["id"].eq(id_titulo)].iloc[0]
        resgates_titulo = resgates.loc[resgates["id"].eq(id_titulo)].sort_values(
            "data_resgate"
        )
        resgate_total = False

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
            # Remove as linhas no dia e após o resgate, pois terão que ser
            # recalculadas. Dependendo do saldo restante, pode ser necessário
            # adicionar novos valores.
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
                resgate_total = True

        patrimonio_rf.append(valor_titulo)

        # Definindo informações da carteira
        fim_titulo = 1 if date.today() >= aporte["data_venc"] else 0
        carteira_rf["id"].append(aporte["id"])
        carteira_rf["data_atualizacao"].append(valor_titulo["data"].iloc[-1])
        carteira_rf["saldo"].append(
            0 if resgate_total or fim_titulo else valor_titulo["valor"].iloc[-1]
        )
        carteira_rf["resgates"].append(
            resgates_titulo["valor"].sum() if not resgates_titulo.empty else 0
        )
        carteira_rf["rendimentos_bruto"].append(valor_titulo["rendimento"].sum())
        carteira_rf["status"].append(0 if resgate_total or fim_titulo else 1)

    patrimonio_rf = pd.concat(patrimonio_rf, ignore_index=True)
    carteira_rf = pd.DataFrame(carteira_rf)
    return patrimonio_rf, carteira_rf


def obter_serie_variacao(
    cotacoes: pd.DataFrame, data_inicio: date, data_fim: date, codigo: str
) -> pd.Series:
    # O filtro lt na data_fim é porque a data de vencimento é como se fosse um dia de
    # resgate, ou seja, o valor que será devolvido é o do dia anterior. Por isso, só
    # faz sentido calcular o patrimônio até o dia anterior.
    mascara_datas = cotacoes["data"].ge(data_inicio) & cotacoes["data"].lt(data_fim)
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

        fator_diario = pd.Series(
            (taxa + 1) ** (1 / 252), index=dias_uteis, name="variacao"
        )
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
