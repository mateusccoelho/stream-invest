import locale

import pandas as pd

from src.dashboard.constants import CATEGORIAS_ATIVOS

locale.setlocale(locale.LC_ALL, "pt_BR")


def formatar_dinheiro(valor: float) -> str:
    return locale.currency(valor, grouping=True, symbol="R$")


def formatar_porcentagem(valor: float) -> str:
    return "{:.2f}%".format(valor * 100)


def formatar_df_proventos_ativo(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["ultimo_pag"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    for col in ["total"]:
        df[col] = df[col].apply(formatar_dinheiro)

    for col in ["yoc_periodo"]:
        df[col] = df[col].apply(formatar_porcentagem)

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
    return df


def formatar_df_proventos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["dt_pag"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    for col in ["valor", "total"]:
        df[col] = df[col].apply(formatar_dinheiro)

    for col in ["yoc_anualizado"]:
        df[col] = df[col].apply(formatar_porcentagem)

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
    return df


def formatar_df_rebalanceamento(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["porcent_alvo", "porcent_atual"]:
        df[col] = df[col].apply(formatar_porcentagem)

    for col in ["valor_alvo", "valor_atual", "delta"]:
        df[col] = df[col].apply(formatar_dinheiro)

    df["tipo"] = df["tipo"].replace(CATEGORIAS_ATIVOS)

    df = df.rename(
        columns={
            "tipo": "Classe de ativos",
            "porcent_alvo": "Porcentagem alvo",
            "porcent_atual": "Porcentagem atual",
            "valor_alvo": "Valor alvo",
            "valor_atual": "Valor atual",
            "delta": "Investir",
        }
    )
    return df


def formatar_df_renda_fixa(df: pd.DataFrame, inativos=False) -> pd.DataFrame:
    df = df.copy()

    for col in ["data_compra", "data_venc", "data_atualizacao"]:
        df[col] = pd.to_datetime(df[col])

    df = df.sort_values("data_venc")

    # Esse tratamento separado é necessário pois não pode ser executado antes da
    # ordenação por data de vencimento.
    for col in ["data_compra", "data_venc", "data_atualizacao"]:
        df[col] = df[col].dt.strftime("%d/%m/%Y")

    for col in ["taxa", "retorno"]:
        df[col] = df[col].apply(formatar_porcentagem)
    df["status"] = df["status"].map({1: "Sim", 0: "Não"})

    for col in ["valor", "saldo", "rendimentos_bruto", "resgates"]:
        df[col] = df[col].apply(formatar_dinheiro)

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

    return df.filter(cols_to_show)


def formatar_df_renda_var(df: pd.DataFrame, inativos=False) -> pd.DataFrame:
    df = df.copy().reset_index().sort_values("bench")

    for col in ["data"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    for col in ["preco_medio", "preco_atual", "rendimento_total", "patrimonio"]:
        df[col] = df[col].apply(formatar_dinheiro)

    for col in ["retorno"]:
        df[col] = df[col].apply(formatar_porcentagem)

    return df.filter(
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
        }
    )


def formatar_df_resgates(resgates: pd.DataFrame) -> pd.DataFrame:
    resgates = resgates.copy()

    for col in ["data_resgate"]:
        resgates[col] = pd.to_datetime(resgates[col]).dt.strftime("%d/%m/%Y")

    for col in ["valor"]:
        resgates[col] = resgates[col].apply(formatar_dinheiro)

    return resgates.filter(["data_resgate", "valor"]).rename(
        columns={
            "data_resgate": "Data",
            "valor": "Valor",
        }
    )


def formatar_transacoes_rv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["data"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    for col in ["preco", "taxas"]:
        df[col] = df[col].apply(formatar_dinheiro)

    df["tipo"] = df["tipo"].replace({"C": "Compra", "V": "Venda"})

    return df.filter(
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


def formatar_df_taxas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["taxa", "taxa_desc"]:
        df[col] = df[col].apply(formatar_porcentagem)

    for col in ["valor"]:
        df[col] = df[col].apply(formatar_dinheiro)

    return df.filter(
        ["id", "tipo", "faixa_prazo", "taxa", "taxa_desc", "valor"]
    ).rename(
        columns={
            "id": "ID",
            "tipo": "Tipo",
            "taxa": "Taxa",
            "faixa_prazo": "Prazo",
            "taxa_desc": "Taxa descontada",
            "valor": "Valor",
        }
    )


def formatar_df_taxas_agg(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["proporcao", "taxa_media", "taxa_alvo"]:
        df[col] = df[col].apply(formatar_porcentagem)

    for col in ["valor"]:
        df[col] = df[col].apply(formatar_dinheiro)

    return df.rename(
        columns={
            "faixa_prazo": "Prazo",
            "proporcao": "Proporção",
            "taxa_media": "Taxa média",
            "valor": "Valor",
            "taxa_alvo": "Taxa alvo",
        }
    )
