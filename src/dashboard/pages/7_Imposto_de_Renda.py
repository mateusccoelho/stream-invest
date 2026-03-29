import streamlit as st

from src.dashboard.dados import carregar_dados, calcular_ir_etfs
from src.dashboard.formatacao import formatar_dinheiro, formatar_ir_etfs


def pagina_imposto_de_renda(ir_df):
    st.markdown("# Imposto de Renda — ETFs")
    st.caption("IR de 15% sobre o lucro na venda de ETFs de renda variável")

    if ir_df.empty:
        st.info("Nenhuma venda de ETF registrada.")
        return

    ir_total = ir_df["ir"].sum()
    lucro_total = ir_df["lucro"].sum()
    qtd_vendas = ir_df.shape[0]

    cols = st.columns(3)
    cols[0].metric("IR total devido", formatar_dinheiro(ir_total))
    cols[1].metric("Lucro/Prejuízo total", formatar_dinheiro(lucro_total))
    cols[2].metric("Quantidade de vendas", qtd_vendas)

    df_fmt, col_config = formatar_ir_etfs(ir_df)
    st.dataframe(
        df_fmt,
        column_config=col_config,
        hide_index=True,
        width="stretch",
    )


dados = carregar_dados()
ir_df = calcular_ir_etfs(
    transacoes_rv=dados["transacoes_rv"],
    ativos_rv=dados["ativos_rv"],
    patrimonio_rv=dados["patrimonio_rv"],
)
pagina_imposto_de_renda(ir_df)
