import pandas as pd
import streamlit as st

from src.dashboard.dados import (
    carregar_dados,
    calcular_ir_etfs,
    calcular_posicao_fim_ano,
    montar_tabela_mensal_ir,
)
from src.dashboard.formatacao import (
    formatar_dinheiro,
    formatar_ir_etfs,
    formatar_posicao_fim_ano,
    formatar_tabela_mensal_ir,
)


def pagina_imposto_de_renda(
    ir_df: pd.DataFrame,
    tabela_mensal: pd.DataFrame,
    patrimonio_rv: pd.DataFrame,
):
    st.markdown("# Imposto de Renda — ETFs")
    st.caption("IR de 15% sobre o lucro na venda de ETFs de renda variável")

    ir_total = ir_df["ir"].sum() if not ir_df.empty else 0
    lucro_total = ir_df["lucro"].sum() if not ir_df.empty else 0
    qtd_vendas = ir_df.shape[0]
    total_pago = tabela_mensal["ir_pago"].sum() if not tabela_mensal.empty else 0

    cols = st.columns(4)
    cols[0].metric("IR total devido", formatar_dinheiro(ir_total))
    cols[1].metric("Lucro/Prejuízo total", formatar_dinheiro(lucro_total))
    cols[2].metric("Quantidade de vendas", qtd_vendas)
    cols[3].metric("Total pago (DARFs)", formatar_dinheiro(total_pago))

    if not ir_df.empty:
        st.subheader("Vendas detalhadas")
        df_fmt, col_config = formatar_ir_etfs(ir_df)
        st.dataframe(df_fmt, column_config=col_config, hide_index=True, width="stretch")

        st.subheader("Acompanhamento mensal")
        df_fmt, col_config = formatar_tabela_mensal_ir(tabela_mensal)
        st.dataframe(df_fmt, column_config=col_config, hide_index=True, width="content")

    # --- Posição dos ativos em 31/12 ---
    st.markdown("---")
    st.subheader("Posição de renda variável em 31/12")
    st.caption("Quantidade × preço médio de compra na data de referência")

    ano_min = patrimonio_rv["data"].min().year
    ano_max = patrimonio_rv["data"].max().year - 1
    anos_disponiveis = list(range(ano_max, ano_min - 1, -1))

    ano_selecionado = st.selectbox("Ano", anos_disponiveis, key="ano_posicao_ir")

    posicao = calcular_posicao_fim_ano(patrimonio_rv, ano_selecionado)

    if posicao.empty:
        st.info(f"Nenhuma posição encontrada para 31/12/{ano_selecionado}.")
    else:
        df_fmt, col_config = formatar_posicao_fim_ano(posicao)
        st.dataframe(df_fmt, column_config=col_config, hide_index=True, width="content")


dados = carregar_dados()
ir_df = calcular_ir_etfs(
    transacoes_rv=dados["transacoes_rv"],
    ativos_rv=dados["ativos_rv"],
    patrimonio_rv=dados["patrimonio_rv"],
)
tabela_mensal = montar_tabela_mensal_ir(
    ir_df,
    dados["pagamentos_ir"],
)
pagina_imposto_de_renda(
    ir_df,
    tabela_mensal,
    patrimonio_rv=dados["patrimonio_rv"],
)
