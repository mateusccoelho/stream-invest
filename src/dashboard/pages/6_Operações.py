"""
Página para cadastro de novas operações diretamente pelo dashboard.
"""

import sys

sys.path.append("..")

from datetime import date

import streamlit as st

from src.database import (
    inserir_aporte_rf,
    inserir_resgate_rf,
    inserir_transacao_rv,
    inserir_provento_rv,
    inserir_ativo_rv,
    inserir_proporcao,
    proximo_id_aporte_rf,
    listar_codigos_rv,
    listar_ids_aportes_rf_ativos,
    ler_proporcoes,
    ler_aportes_rf,
)
from src.dashboard.formatacao import formatar_dinheiro

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Operações",
    page_icon=":pencil:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("# Cadastro de Operações")
st.caption(
    "Adicione novas operações ao banco de dados. "
    "Após cadastrar, reinicie o dashboard para ver os dados atualizados."
)

# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "Aporte RF",
    "Resgate RF",
    "Transação RV",
    "Provento RV",
    "Ativo RV",
    "Proporções",
])

# ===== ABA 1 – Aporte RF ===================================================
with tabs[0]:
    st.markdown("### Novo aporte de renda fixa")
    prox_id = proximo_id_aporte_rf()
    st.info(f"Próximo ID disponível: **{prox_id}**")

    with st.form("form_aporte_rf", clear_on_submit=True):
        cols = st.columns(3)
        corretora = cols[0].text_input("Corretora")
        emissor = cols[1].text_input("Emissor")
        tipo_rf = cols[2].selectbox("Tipo", ["CDB", "LCI", "LCA"])

        cols2 = st.columns(3)
        forma = cols2[0].selectbox("Forma", ["Pós", "Pré"])
        indexador = cols2[1].selectbox("Indexador", ["CDI", "Pré", "IPCA +"])
        taxa = cols2[2].number_input("Taxa (%)", min_value=0.0, step=0.01, format="%.4f")

        cols3 = st.columns(3)
        data_compra = cols3[0].date_input("Data de compra", value=date.today())
        data_vencimento = cols3[1].date_input("Data de vencimento", value=date.today())
        valor = cols3[2].number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")

        reserva = st.checkbox("Reserva de emergência")
        submitted = st.form_submit_button("💾 Cadastrar aporte", use_container_width=True)

        if submitted:
            if not corretora or not emissor:
                st.error("Preencha corretora e emissor.")
            elif data_vencimento <= data_compra:
                st.error("Data de vencimento deve ser posterior à data de compra.")
            else:
                novo_id = inserir_aporte_rf(
                    corretora=corretora,
                    emissor=emissor,
                    tipo=tipo_rf,
                    forma=forma,
                    data_compra=data_compra,
                    data_vencimento=data_vencimento,
                    indexador=indexador,
                    taxa=taxa,
                    valor=valor,
                    reserva=reserva,
                )
                st.success(f"Aporte cadastrado com ID **{novo_id}**!")

# ===== ABA 2 – Resgate RF ==================================================
with tabs[1]:
    st.markdown("### Novo resgate de renda fixa")

    ids_ativos = listar_ids_aportes_rf_ativos()
    if not ids_ativos:
        st.warning("Não há aportes RF ativos para resgatar.")
    else:
        # Mostra resumo dos aportes ativos
        aportes_df = ler_aportes_rf()
        aportes_ativos = aportes_df[aportes_df["id"].isin(ids_ativos)]
        with st.expander("Ver aportes ativos"):
            st.dataframe(
                aportes_ativos[["id", "emissor", "tipo", "index", "taxa", "valor", "data_compra", "data_venc"]],
                hide_index=True,
                use_container_width=True,
            )

        with st.form("form_resgate_rf", clear_on_submit=True):
            cols = st.columns(3)
            id_resgate = cols[0].selectbox("ID do aporte", ids_ativos)
            data_resgate = cols[1].date_input("Data do resgate", value=date.today())
            valor_resgate = cols[2].number_input(
                "Valor resgatado (R$)", min_value=0.01, step=0.01, format="%.2f"
            )
            final = st.checkbox("Resgate total (final)")
            submitted = st.form_submit_button("💾 Cadastrar resgate", use_container_width=True)

            if submitted:
                inserir_resgate_rf(
                    id_aporte=id_resgate,
                    data_resgate=data_resgate,
                    valor=valor_resgate,
                    final=final,
                )
                st.success(
                    f"Resgate de {formatar_dinheiro(valor_resgate)} do aporte "
                    f"**{id_resgate}** cadastrado!"
                )

# ===== ABA 3 – Transação RV ================================================
with tabs[2]:
    st.markdown("### Nova transação de renda variável")

    codigos = listar_codigos_rv()

    with st.form("form_transacao_rv", clear_on_submit=True):
        cols = st.columns(4)
        data_trans = cols[0].date_input("Data", value=date.today())
        if codigos:
            codigo_trans = cols[1].selectbox("Código do ativo", codigos)
        else:
            codigo_trans = cols[1].text_input("Código do ativo")
        operacao = cols[2].selectbox("Operação", ["C", "V"], format_func=lambda x: "Compra" if x == "C" else "Venda")
        corretora_rv = cols[3].text_input("Corretora")

        cols2 = st.columns(3)
        qtd_trans = cols2[0].number_input("Quantidade", min_value=1, step=1)
        preco_trans = cols2[1].number_input("Preço unitário (R$)", min_value=0.01, step=0.01, format="%.2f")
        taxas_trans = cols2[2].number_input("Taxas (R$)", min_value=0.0, step=0.01, format="%.2f", value=0.0)

        submitted = st.form_submit_button("💾 Cadastrar transação", use_container_width=True)

        if submitted:
            if not codigo_trans or not corretora_rv:
                st.error("Preencha o código do ativo e a corretora.")
            else:
                inserir_transacao_rv(
                    data=data_trans,
                    codigo=codigo_trans,
                    operacao=operacao,
                    quantidade=qtd_trans,
                    preco=preco_trans,
                    corretora=corretora_rv,
                    taxas=taxas_trans,
                )
                valor_total = qtd_trans * preco_trans
                st.success(
                    f"Transação de {'compra' if operacao == 'C' else 'venda'} "
                    f"de **{qtd_trans}x {codigo_trans}** ({formatar_dinheiro(valor_total)}) cadastrada!"
                )

# ===== ABA 4 – Provento RV =================================================
with tabs[3]:
    st.markdown("### Novo provento de renda variável")

    codigos = listar_codigos_rv()

    with st.form("form_provento_rv", clear_on_submit=True):
        cols = st.columns(4)
        data_prov = cols[0].date_input("Data de pagamento", value=date.today())
        if codigos:
            codigo_prov = cols[1].selectbox("Código do ativo", codigos)
        else:
            codigo_prov = cols[1].text_input("Código do ativo")
        qtd_prov = cols[2].number_input("Quantidade", min_value=1, step=1)
        valor_prov = cols[3].number_input("Valor unitário (R$)", min_value=0.01, step=0.0001, format="%.4f")

        tipo_prov = st.selectbox("Tipo", ["Rendimento"])
        submitted = st.form_submit_button("💾 Cadastrar provento", use_container_width=True)

        if submitted:
            if not codigo_prov:
                st.error("Preencha o código do ativo.")
            else:
                inserir_provento_rv(
                    data_pagamento=data_prov,
                    codigo=codigo_prov,
                    quantidade=qtd_prov,
                    valor=valor_prov,
                    tipo=tipo_prov,
                )
                st.success(
                    f"Provento de **{codigo_prov}** "
                    f"({formatar_dinheiro(qtd_prov * valor_prov)}) cadastrado!"
                )

# ===== ABA 5 – Ativo RV ====================================================
with tabs[4]:
    st.markdown("### Cadastrar / atualizar ativo de renda variável")

    with st.form("form_ativo_rv", clear_on_submit=True):
        cols = st.columns(3)
        codigo_ativo = cols[0].text_input("Código do ativo")
        tipo_ativo = cols[1].selectbox("Tipo", ["Ação", "ETF", "FII", "FI-Infra"])
        benchmark = cols[2].text_input("Benchmark")

        submitted = st.form_submit_button("💾 Cadastrar ativo", use_container_width=True)

        if submitted:
            if not codigo_ativo or not benchmark:
                st.error("Preencha o código e o benchmark.")
            else:
                inserir_ativo_rv(
                    codigo=codigo_ativo.upper(),
                    tipo=tipo_ativo,
                    benchmark=benchmark,
                )
                st.success(f"Ativo **{codigo_ativo.upper()}** cadastrado/atualizado!")

# ===== ABA 6 – Proporções ==================================================
with tabs[5]:
    st.markdown("### Proporções alvo da carteira")

    proporcoes_atuais = ler_proporcoes()
    if not proporcoes_atuais.empty:
        st.markdown("##### Proporções atuais")
        display_df = proporcoes_atuais.copy()
        display_df["proporcao"] = display_df["proporcao"].apply(lambda x: f"{x*100:.1f}%")
        display_df.columns = ["Classe", "Proporção"]
        st.dataframe(display_df, hide_index=True, use_container_width=True)

    with st.form("form_proporcao", clear_on_submit=True):
        cols = st.columns(2)
        classe = cols[0].text_input("Classe de ativos")
        proporcao = cols[1].number_input(
            "Proporção (0.0 a 1.0)", min_value=0.0, max_value=1.0, step=0.01, format="%.4f"
        )
        submitted = st.form_submit_button("💾 Cadastrar/atualizar proporção", use_container_width=True)

        if submitted:
            if not classe:
                st.error("Preencha a classe de ativos.")
            else:
                inserir_proporcao(classe=classe, proporcao=proporcao)
                st.success(f"Proporção de **{classe}** atualizada para {proporcao*100:.1f}%!")
                st.rerun()
