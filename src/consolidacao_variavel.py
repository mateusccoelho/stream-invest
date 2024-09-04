from datetime import date
from typing import List

import pandas as pd

from src.utils.calendario import calcular_dias_uteis_entre


def calcula_qtd_preco_medio(df: pd.DataFrame) -> pd.DataFrame:
    """Assume-se que o df passado está ordernado por ativo e data nessa ordem.
    É retornardo um DF com duas colunas, a quantidade acumulada e o preço médio.
    """
    
    qtd, preco_medio = [0], [0] 
    for qtd_sinal, valor_trans in zip(df["qtd_sinal"], df["valor_trans"]):
        nova_qtd = qtd[-1] + qtd_sinal
        if qtd_sinal > 0:
            preco_medio.append(
                (preco_medio[-1] * qtd[-1] + valor_trans) / nova_qtd
            )
        else:
            preco_medio.append(preco_medio[-1])
        qtd.append(nova_qtd)

    return pd.DataFrame({
        "qtd_acum": qtd[1:], 
        "preco_medio": preco_medio[1:]
    })


def consolidar_renda_variavel(
    transacoes_rv: pd.DataFrame,
    cotacoes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Essa função por enquanto não suporta operações de compra e venda
    de um ativo no mesmo dia. Também não zerar a posição de um ativo.
    """

    transacoes_rv["valor_trans"] = (
        transacoes_rv["qtd"] * transacoes_rv["preco"] + transacoes_rv["taxas"]
    )
    transacoes_rv["qtd_sinal"] = (
        transacoes_rv["tipo"].apply(lambda x: 1 if x == "C" else -1)
        * transacoes_rv["qtd"]
    )

    # Calcula o preço médio e a quantidade acumulada em cada que houve operações
    transacoes_rv_agg = (
        transacoes_rv.groupby(["codigo", "data"], as_index=False)
        .sum()
        .filter(["data", "codigo", "qtd", "qtd_sinal", "valor_trans"])
    )
    preco_medio = (
        transacoes_rv_agg.groupby(["codigo"])
        .apply(calcula_qtd_preco_medio, include_groups=False)
        .reset_index()
        .drop(columns=["codigo", "level_1"])
    )
    preco_medio = pd.concat([transacoes_rv_agg, preco_medio], axis=1)

    # Cria uma tabela com todos os dias úteis entre a primeira transação e 
    # o dia de hoje
    primeira_trans = transacoes_rv_agg.groupby("codigo")["data"].min().to_dict()
    dias = pd.concat([
        pd.DataFrame({
            "codigo": codigo, 
            "data": calcular_dias_uteis_entre(data_ini, date.today())
        })
        for codigo, data_ini in primeira_trans.items()
    ], axis=0)

    # Contrói a tabela de patrimônio. O ffill serve para propagar os valores das linhas
    # com transações para as próximas que estão vazias. Não é necessário group by aqui
    # porque a primeira linha de cada ativo é sempre preenchida, assim o ffill não 
    # "atravessa" os ativos.
    patrimonio_rv = (
        dias.merge(preco_medio, how="left", on=["codigo", "data"])
        .merge(cotacoes, how="left", on=["codigo", "data"])
    )
    for col in ["qtd_acum", "preco_medio"]:
        patrimonio_rv[col] = patrimonio_rv[col].ffill()

    # O rendimento é o patrimonio de hoje menos o do dia anterior. Nos dias em 
    # que houveram operações o valor transacionado é levado em conta.
    # No caso das compras, seria adicionar o valor transacionado ao patrimonio 
    # anterior e subtrair do atual? No caso de vendas, eu uso o preço médio ou
    # o preço do dia? Porque preciso calcular o rendimento?
    patrimonio_rv["patrimonio"] = patrimonio_rv["qtd_acum"] * patrimonio_rv["valor"]
    # patrimonio_rv["patrimonio_ant"] = patrimonio_rv.groupby("codigo")["patrimonio"].shift(1).fillna(0)
    # patrimonio_rv["rendimento"] = (
    #     patrimonio_rv["patrimonio"] - patrimonio_rv["patrimonio_ant"]
    # )

    patrimonio_rv = (
        patrimonio_rv.drop(
            columns=["variacao", "valor", "qtd", "qtd_sinal", "valor_trans"]
        )
        .rename(columns={"qtd_acum": "qtd"})
    )
    
    carteira_rv = (
        patrimonio_rv.groupby("codigo")
        .last()
        .assign(status=1)
    )
    carteira_rv["rendimento_total"] = (
        carteira_rv["patrimonio"] - carteira_rv["preco_medio"] * carteira_rv["qtd"]
    )
    return patrimonio_rv, carteira_rv
