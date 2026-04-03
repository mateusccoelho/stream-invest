import pandas as pd
import streamlit as st

from src.dashboard.dados import (
    carregar_dados,
    calcular_ir_etfs,
    montar_tabela_mensal_ir,
)
from src.dashboard.formatacao import (
    formatar_dinheiro,
    formatar_ir_etfs,
    formatar_tabela_mensal_ir,
)


def pagina_imposto_de_renda(
    ir_df: pd.DataFrame,
    tabela_mensal: pd.DataFrame,
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
        st.dataframe(df_fmt, column_config=col_config, hide_index=True)


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
pagina_imposto_de_renda(ir_df, tabela_mensal)
