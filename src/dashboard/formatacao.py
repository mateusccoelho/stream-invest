import locale
from typing import Tuple

import pandas as pd
import streamlit as st

locale.setlocale(locale.LC_ALL, "pt_BR")

DfComConfig = Tuple[pd.DataFrame, dict]


# Formatação de valores individuais (para métricas, textos)


def formatar_dinheiro(valor: float) -> str:
    return locale.currency(valor, grouping=True, symbol="R$")


def formatar_porcentagem(valor: float) -> str:
    return "{:.2f}%".format(valor * 100)


# Helpers para column_config


def _col_dinheiro(label: str) -> st.column_config.NumberColumn:
    return st.column_config.NumberColumn(label, format="R$ %.2f")


def _col_porcentagem(label: str) -> st.column_config.NumberColumn:
    return st.column_config.NumberColumn(label, format="%.2f%%")


def _col_data(label: str) -> st.column_config.DateColumn:
    return st.column_config.DateColumn(label, format="DD/MM/YYYY")


# Funções de formatação de DataFrames


def formatar_df_proventos_ativo(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["ultimo_pag"]:
        df[col] = pd.to_datetime(df[col])

    for col in ["yoc_periodo"]:
        df[col] = df[col] * 100

    df = df.filter(
        ["codigo", "tipo_ativo", "total", "yoc_periodo", "qtd", "ultimo_pag"]
    ).rename(
        columns={
            "codigo": "Código",
            "tipo_ativo": "Tipo",
            "total": "Total recebido/provisionado",
            "qtd": "# Pagamentos",
            "ultimo_pag": "Último pagamento",
            "yoc_periodo": "YoC período",
        }
    )

    column_config = {
        "Total recebido/provisionado": _col_dinheiro("Total recebido/provisionado"),
        "YoC período": _col_porcentagem("YoC período"),
        "Último pagamento": _col_data("Último pagamento"),
    }
    return df, column_config


def formatar_df_proventos(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["dt_pag"]:
        df[col] = pd.to_datetime(df[col])

    for col in ["yoc_anualizado"]:
        df[col] = df[col] * 100

    df = df.filter(
        ["dt_pag", "codigo", "qtd", "valor", "yoc_anualizado", "total", "tipo"]
    ).rename(
        columns={
            "dt_pag": "Data de pagamento",
            "tipo": "Tipo",
            "codigo": "Código",
            "qtd": "Quantidade",
            "valor": "Valor",
            "total": "Total",
            "yoc_anualizado": "YoC anualizado",
        }
    )

    column_config = {
        "Valor": _col_dinheiro("Valor"),
        "Total": _col_dinheiro("Total"),
        "YoC anualizado": _col_porcentagem("YoC anualizado"),
        "Data de pagamento": _col_data("Data de pagamento"),
    }
    return df, column_config


def formatar_df_rebalanceamento(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["proporcao", "porcent_atual"]:
        df[col] = df[col] * 100

    df = df.rename(
        columns={
            "classe": "Classe de ativos",
            "proporcao": "Porcentagem alvo",
            "porcent_atual": "Porcentagem atual",
            "valor_alvo": "Valor alvo",
            "valor_atual": "Valor atual",
            "delta": "Investir",
        }
    )

    column_config = {
        "Porcentagem alvo": _col_porcentagem("Porcentagem alvo"),
        "Porcentagem atual": _col_porcentagem("Porcentagem atual"),
        "Valor alvo": _col_dinheiro("Valor alvo"),
        "Valor atual": _col_dinheiro("Valor atual"),
        "Investir": _col_dinheiro("Investir"),
    }
    return df, column_config


def formatar_df_renda_fixa(df: pd.DataFrame, inativos=False) -> DfComConfig:
    df = df.copy()

    for col in ["data_compra", "data_venc", "data_atualizacao"]:
        df[col] = pd.to_datetime(df[col])

    df = df.sort_values("data_venc")

    for col in ["taxa", "retorno"]:
        df[col] = df[col] * 100

    df["status"] = df["status"].map({1: "Sim", 0: "Não"})

    df = df.reset_index().rename(
        columns={
            "id": "ID",
            "tipo": "Tipo",
            "emissor": "Emissor",
            "index": "Forma",
            "taxa": "Taxa",
            "data_venc": "Vencimento",
            "valor": "Investido",
            "saldo": "Saldo",
            "rendimentos_bruto": "Rendimentos",
            "status": "Ativo",
            "retorno": "Retorno",
            "resgates": "Resgates",
            "data_compra": "Compra",
            "data_atualizacao": "Atualização",
        }
    )

    cols_to_show = [
        "ID",
        "Tipo",
        "Emissor",
        "Forma",
        "Taxa",
        "Compra",
        "Vencimento",
        "Investido",
        "Resgates",
        "Saldo",
        "Rendimentos",
        "Retorno",
        "Atualização",
    ]
    if inativos:
        cols_to_show.append("Ativo")

    column_config = {
        "Taxa": _col_porcentagem("Taxa"),
        "Retorno": _col_porcentagem("Retorno"),
        "Investido": _col_dinheiro("Investido"),
        "Saldo": _col_dinheiro("Saldo"),
        "Rendimentos": _col_dinheiro("Rendimentos"),
        "Resgates": _col_dinheiro("Resgates"),
        "Compra": _col_data("Compra"),
        "Vencimento": _col_data("Vencimento"),
        "Atualização": _col_data("Atualização"),
    }
    return df.filter(cols_to_show), column_config


def formatar_df_renda_var(df: pd.DataFrame, inativos=False) -> DfComConfig:
    df = df.copy().reset_index().sort_values("bench")

    for col in ["data"]:
        df[col] = pd.to_datetime(df[col])

    for col in ["retorno", "retorno_com_proventos"]:
        df[col] = df[col] * 100

    df = df.filter(
        [
            "codigo",
            "tipo",
            "bench",
            "qtd",
            "preco_medio",
            "preco_atual",
            "patrimonio",
            "rendimento_total",
            "retorno",
            "total_proventos",
            "retorno_com_proventos",
            "data",
        ]
    ).rename(
        columns={
            "preco_medio": "Preço médio",
            "preco_atual": "Preço atual",
            "rendimento_total": "Variação total",
            "patrimonio": "Patrimônio",
            "data": "Atualização",
            "qtd": "Quantidade",
            "bench": "Benchmark",
            "codigo": "Código",
            "tipo": "Tipo",
            "retorno": "Retorno",
            "total_proventos": "Proventos",
            "retorno_com_proventos": "Retorno com proventos",
        }
    )

    column_config = {
        "Preço médio": _col_dinheiro("Preço médio"),
        "Preço atual": _col_dinheiro("Preço atual"),
        "Variação total": _col_dinheiro("Variação total"),
        "Patrimônio": _col_dinheiro("Patrimônio"),
        "Proventos": _col_dinheiro("Proventos"),
        "Retorno": _col_porcentagem("Retorno"),
        "Retorno com proventos": _col_porcentagem("Retorno com proventos"),
        "Atualização": _col_data("Atualização"),
    }
    return df, column_config


def formatar_df_resgates(resgates: pd.DataFrame) -> DfComConfig:
    resgates = resgates.copy()

    for col in ["data_resgate"]:
        resgates[col] = pd.to_datetime(resgates[col])

    resgates = resgates.filter(["data_resgate", "valor"]).rename(
        columns={
            "data_resgate": "Data",
            "valor": "Valor",
        }
    )

    column_config = {
        "Valor": _col_dinheiro("Valor"),
        "Data": _col_data("Data"),
    }
    return resgates, column_config


def formatar_transacoes_rv(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["data"]:
        df[col] = pd.to_datetime(df[col])

    df["tipo"] = df["tipo"].replace({"C": "Compra", "V": "Venda"})

    df = df.filter(
        ["codigo", "data", "tipo", "qtd", "preco", "taxas", "corretora"]
    ).rename(
        columns={
            "codigo": "Código",
            "data": "Data",
            "tipo": "Operação",
            "qtd": "Quantidade",
            "preco": "Preço",
            "taxas": "Taxa total",
            "corretora": "Corretora",
        }
    )

    column_config = {
        "Preço": _col_dinheiro("Preço"),
        "Taxa total": _col_dinheiro("Taxa total"),
        "Data": _col_data("Data"),
    }
    return df, column_config


def formatar_df_taxas(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["taxa", "taxa_desc"]:
        df[col] = df[col] * 100

    df = df.filter(["id", "tipo", "faixa_prazo", "taxa", "taxa_desc", "valor"]).rename(
        columns={
            "id": "ID",
            "tipo": "Tipo",
            "taxa": "Taxa",
            "faixa_prazo": "Prazo",
            "taxa_desc": "Taxa descontada",
            "valor": "Valor",
        }
    )

    column_config = {
        "Taxa": _col_porcentagem("Taxa"),
        "Taxa descontada": _col_porcentagem("Taxa descontada"),
        "Valor": _col_dinheiro("Valor"),
    }
    return df, column_config


def formatar_df_taxas_agg(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["proporcao", "taxa_media", "taxa_alvo"]:
        df[col] = df[col] * 100

    df = df.rename(
        columns={
            "faixa_prazo": "Prazo",
            "proporcao": "Proporção",
            "taxa_media": "Taxa média",
            "valor": "Valor",
            "taxa_alvo": "Taxa alvo",
        }
    )

    column_config = {
        "Proporção": _col_porcentagem("Proporção"),
        "Taxa média": _col_porcentagem("Taxa média"),
        "Taxa alvo": _col_porcentagem("Taxa alvo"),
        "Valor": _col_dinheiro("Valor"),
    }
    return df, column_config


def formatar_ir_etfs(df: pd.DataFrame) -> DfComConfig:
    df = df.copy()

    for col in ["data_venda"]:
        df[col] = pd.to_datetime(df[col])

    df = df.rename(
        columns={
            "data_venda": "Data da venda",
            "codigo": "Código",
            "qtd": "Quantidade",
            "preco_venda": "Preço de venda",
            "taxas_venda": "Taxas",
            "valor_venda_liq": "Valor líquido",
            "preco_medio": "Preço médio",
            "custo": "Custo",
            "lucro": "Lucro/Prejuízo",
            "ir": "IR devido",
        }
    )

    column_config = {
        "Data da venda": _col_data("Data da venda"),
        "Preço de venda": _col_dinheiro("Preço de venda"),
        "Taxas": _col_dinheiro("Taxas"),
        "Valor líquido": _col_dinheiro("Valor líquido"),
        "Preço médio": _col_dinheiro("Preço médio"),
        "Custo": _col_dinheiro("Custo"),
        "Lucro/Prejuízo": _col_dinheiro("Lucro/Prejuízo"),
        "IR devido": _col_dinheiro("IR devido"),
    }
    return df, column_config
