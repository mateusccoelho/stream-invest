import locale

locale.setlocale(locale.LC_ALL, "pt_BR")

import pandas as pd


def formatar_dinheiro(valor: float) -> str:
    return locale.currency(valor, grouping=True, symbol="R$")


def formatar_df_proventos_ativo(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["ultimo_pag"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    for col in ["total"]:
        df[col] = df[col].apply(formatar_dinheiro)

    df = df.reset_index().rename(
        columns={
            "codigo": "Código",
            "total": "Total recebido/provisionado",
            "qtd": "# Pagamentos",
            "ultimo_pag": "Último pagamento",
        }
    )
    return df


def formatar_df_proventos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["dt_pag"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    for col in ["valor", "total"]:
        df[col] = df[col].apply(formatar_dinheiro)

    df = df.filter(["dt_pag", "codigo", "qtd", "valor", "total", "tipo"]).rename(
        columns={
            "dt_pag": "Data de pagamento",
            "tipo": "Tipo",
            "codigo": "Código",
            "qtd": "Quantidade",
            "valor": "Valor",
            "total": "Total",
        }
    )
    return df


def formatar_df_renda_fixa(df: pd.DataFrame, inativos=False) -> pd.DataFrame:
    df = df.copy()

    for col in ["data_compra", "data_vencimento", "data_atualizacao"]:
        df[col] = pd.to_datetime(df[col])

    df = df.sort_values("data_vencimento").reset_index()

    for col in ["data_compra", "data_vencimento", "data_atualizacao"]:
        df[col] = df[col].dt.strftime("%d/%m/%Y")

    for col in ["taxa", "retorno"]:
        df[col] = df[col].apply(lambda x: "{:.2f}".format(x * 100)) + "%"
    df["status"] = df["status"].map({1: "Sim", 0: "Não"})

    for col in ["valor_aplicado", "saldo", "rendimentos_bruto", "resgates"]:
        df[col] = df[col].apply(formatar_dinheiro)

    df = df.rename(
        columns={
            "id_titulo": "ID",
            "tipo": "Tipo",
            "emissor": "Emissor",
            "indexador": "Forma",
            "taxa": "Taxa",
            "data_vencimento": "Vencimento",
            "valor_aplicado": "Investido",
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

    return df[cols_to_show]


def formatar_df_renda_var(df: pd.DataFrame, inativos=False) -> pd.DataFrame:
    df = df.copy().reset_index().sort_values("benchmark")

    for col in ["data_atualizacao"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

    df["status"] = df["status"].map({1: "Sim", 0: "Não"})

    for col in ["preco_medio", "rendimento_hoje", "rendimento_total", "patrimonio"]:
        df[col] = df[col].apply(
            lambda x: locale.currency(x, grouping=True, symbol="R$")
        )

    df = df.rename(
        columns={
            "preco_medio": "Preço médio",
            "rendimento_hoje": "Variação hoje",
            "rendimento_total": "Variação total",
            "patrimonio": "Patrimônio",
            "status": "Ativo",
            "data_atualizacao": "Atualização",
            "quantidade": "Quantidade",
            "benchmark": "Benchmark",
            "codigo": "Código",
            "tipo": "Tipo",
        }
    )

    cols_to_show = [
        "Código",
        "Tipo",
        "Benchmark",
        "Preço médio",
        "Quantidade",
        "Patrimônio",
        "Variação hoje",
        "Variação total",
        "Atualização",
    ]
    if inativos:
        cols_to_show.append("Ativo")

    return df[cols_to_show]
