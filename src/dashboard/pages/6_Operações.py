"""
Página para cadastro de novas operações diretamente pelo dashboard.
"""

import sys

sys.path.append("..")

import streamlit as st

from src.database import (
    inserir_aporte_rf,
    inserir_resgate_rf,
    inserir_transacao_rv,
    inserir_provento_rv,
    inserir_ativo_rv,
    atualizar_proporcoes,
    proximo_id_aporte_rf,
    listar_codigos_rv,
    listar_ids_aportes_rf_ativos,
    ler_proporcoes,
    ler_aportes_rf,
)
from src.dashboard.constants import (
    TIPOS_RF,
    FORMAS_RF,
    INDEXADORES_RF,
    OPERACOES_RV,
    TIPOS_ATIVO_RV,
    TIPOS_PROVENTO_RV,
)
from src.dashboard.formatacao import formatar_dinheiro


def limpar_cache():
    st.cache_data.clear()
    st.cache_resource.clear()


def pagina_operacoes():
    st.markdown("# Cadastro de Operações")
    st.caption(
        "Adicione novas operações ao banco de dados. "
        "Após cadastrar, reinicie o dashboard para ver os dados atualizados."
    )

    tabs = st.tabs(
        [
            "Aporte RF",
            "Resgate RF",
            "Transação RV",
            "Provento RV",
            "Ativo RV",
            "Proporções",
        ]
    )

    # Aporte RF
    with tabs[0]:
        st.markdown("### Novo aporte de renda fixa")
        prox_id = proximo_id_aporte_rf()
        st.info(f"Próximo ID disponível: **{prox_id}**")

        with st.form("form_aporte_rf", clear_on_submit=True):
            cols = st.columns(3)
            corretora = cols[0].text_input("Corretora")
            emissor = cols[1].text_input("Emissor")
            tipo_rf = cols[2].selectbox("Tipo", TIPOS_RF, index=None)

            cols2 = st.columns(3)
            forma = cols2[0].selectbox("Forma", FORMAS_RF, index=None)
            indexador = cols2[1].selectbox("Indexador", INDEXADORES_RF, index=None)
            taxa = cols2[2].number_input(
                "Taxa (%)", min_value=0.0, step=0.01, format="%.4f", value=None
            )

            cols3 = st.columns(3)
            data_compra = cols3[0].date_input("Data de compra", value=None)
            data_vencimento = cols3[1].date_input("Data de vencimento", value=None)
            valor = cols3[2].number_input(
                "Valor (R$)", min_value=0.0, step=0.01, format="%.2f", value=None
            )

            reserva = st.checkbox("Reserva de emergência")
            submitted = st.form_submit_button(
                "💾 Cadastrar aporte", width="stretch"
            )

            if submitted:
                required = [
                    corretora,
                    emissor,
                    tipo_rf,
                    forma,
                    indexador,
                    taxa,
                    data_compra,
                    data_vencimento,
                    valor,
                ]
                if any(
                    x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
                    for x in required
                ):
                    st.write(
                        x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
                        for x in required
                    )
                    st.error("Preencha todos os campos obrigatórios.")
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
                    limpar_cache()

    # Resgate RF
    with tabs[1]:
        st.markdown("### Novo resgate de renda fixa")

        ids_ativos = listar_ids_aportes_rf_ativos()
        if not ids_ativos:
            st.warning("Não há aportes RF ativos para resgatar.")
        else:
            aportes_df = ler_aportes_rf()
            aportes_ativos = aportes_df[aportes_df["id"].isin(ids_ativos)]
            with st.expander("Ver aportes ativos"):
                st.dataframe(
                    aportes_ativos[
                        [
                            "id",
                            "emissor",
                            "tipo",
                            "index",
                            "taxa",
                            "valor",
                            "data_compra",
                            "data_venc",
                        ]
                    ],
                    hide_index=True,
                    width="stretch",
                )

            with st.form("form_resgate_rf", clear_on_submit=True):
                cols = st.columns(3)
                id_resgate = cols[0].selectbox("ID do aporte", ids_ativos, index=None)
                data_resgate = cols[1].date_input("Data do resgate", value=None)
                valor_resgate = cols[2].number_input(
                    "Valor resgatado (R$)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    value=None,
                )
                final = st.checkbox("Resgate total (final)")
                submitted = st.form_submit_button(
                    "💾 Cadastrar resgate", width="stretch"
                )

                if submitted:
                    required = [id_resgate, data_resgate, valor_resgate]
                    if any(
                        x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
                        for x in required
                    ):
                        st.error("Preencha todos os campos obrigatórios.")
                    else:
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
                        limpar_cache()

    # Transação RV
    with tabs[2]:
        st.markdown("### Nova transação de renda variável")

        codigos = listar_codigos_rv()

        with st.form("form_transacao_rv", clear_on_submit=True):
            cols = st.columns(4)
            data_trans = cols[0].date_input("Data", value=None)
            if codigos:
                codigo_trans = cols[1].selectbox("Código do ativo", codigos, index=None)
            else:
                codigo_trans = cols[1].text_input("Código do ativo")
            operacao = cols[2].selectbox(
                "Operação",
                OPERACOES_RV,
                index=None,
                format_func=lambda x: "Compra" if x == "C" else "Venda",
            )
            corretora_rv = cols[3].text_input("Corretora")

            cols2 = st.columns(3)
            qtd_trans = cols2[0].number_input(
                "Quantidade", min_value=0, step=1, value=None
            )
            preco_trans = cols2[1].number_input(
                "Preço unitário (R$)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=None,
            )
            taxas_trans = cols2[2].number_input(
                "Taxas (R$)", min_value=0.0, step=0.01, format="%.2f", value=None
            )

            submitted = st.form_submit_button(
                "💾 Cadastrar transação", width="stretch"
            )

            if submitted:
                required = [
                    data_trans,
                    codigo_trans,
                    operacao,
                    corretora_rv,
                    qtd_trans,
                    preco_trans,
                ]
                if any(
                    x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
                    for x in required
                ):
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    inserir_transacao_rv(
                        data=data_trans,
                        codigo=codigo_trans,
                        operacao=operacao,
                        quantidade=qtd_trans,
                        preco=preco_trans,
                        corretora=corretora_rv,
                        taxas=taxas_trans if taxas_trans is not None else 0.0,
                    )
                    valor_total = qtd_trans * preco_trans
                    st.success(
                        f"Transação de {'compra' if operacao == 'C' else 'venda'} "
                        f"de **{qtd_trans}x {codigo_trans}** ({formatar_dinheiro(valor_total)}) cadastrada!"
                    )
                    limpar_cache()

    # Provento RV
    with tabs[3]:
        st.markdown("### Novo provento de renda variável")

        codigos = listar_codigos_rv()

        with st.form("form_provento_rv", clear_on_submit=True):
            cols = st.columns(4)
            data_prov = cols[0].date_input("Data de pagamento", value=None)
            if codigos:
                codigo_prov = cols[1].selectbox("Código do ativo", codigos, index=None)
            else:
                codigo_prov = cols[1].text_input("Código do ativo")
            qtd_prov = cols[2].number_input(
                "Quantidade", min_value=0, step=1, value=None
            )
            valor_prov = cols[3].number_input(
                "Valor unitário (R$)",
                min_value=0.0,
                step=0.0001,
                format="%.4f",
                value=None,
            )

            tipo_prov = st.selectbox("Tipo", TIPOS_PROVENTO_RV, index=None)
            submitted = st.form_submit_button(
                "💾 Cadastrar provento", width="stretch"
            )

            if submitted:
                required = [data_prov, codigo_prov, qtd_prov, valor_prov, tipo_prov]
                if any(
                    x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
                    for x in required
                ):
                    st.error("Preencha todos os campos obrigatórios.")
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
                    limpar_cache()

    # Ativo RV
    with tabs[4]:
        st.markdown("### Cadastrar / atualizar ativo de renda variável")

        with st.form("form_ativo_rv", clear_on_submit=True):
            cols = st.columns(3)
            codigo_ativo = cols[0].text_input("Código do ativo")
            tipo_ativo = cols[1].selectbox("Tipo", TIPOS_ATIVO_RV, index=None)
            benchmark = cols[2].text_input("Benchmark")

            submitted = st.form_submit_button(
                "💾 Cadastrar ativo", width="stretch"
            )

            if submitted:
                required = [codigo_ativo, tipo_ativo, benchmark]
                if any(x is None or x == "" for x in required):
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    inserir_ativo_rv(
                        codigo=codigo_ativo.upper(),
                        tipo=tipo_ativo,
                        benchmark=benchmark,
                    )
                    st.success(
                        f"Ativo **{codigo_ativo.upper()}** cadastrado/atualizado!"
                    )
                    limpar_cache()

    # Proporções
    with tabs[5]:
        st.markdown("### Proporções alvo da carteira")

        proporcoes_atuais = ler_proporcoes()
        if proporcoes_atuais.empty:
            st.warning("Nenhuma proporção cadastrada.")
        else:
            st.caption("Edite os valores de proporção e clique em salvar.")
            editado = st.data_editor(
                proporcoes_atuais,
                column_config={
                    "classe": st.column_config.TextColumn("Classe", disabled=True),
                    "proporcao": st.column_config.NumberColumn(
                        "Proporção",
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                        format="%.4f",
                    ),
                },
                hide_index=True,
                width="stretch",
                num_rows="fixed",
            )

            if st.button("💾 Salvar proporções", width="stretch"):
                novos_valores = dict(zip(editado["classe"], editado["proporcao"]))
                atualizar_proporcoes(novos_valores)
                st.success("Proporções atualizadas!")
                limpar_cache()


st.set_page_config(
    page_title="Operações",
    page_icon=":pencil:",
    layout="wide",
    initial_sidebar_state="expanded",
)

pagina_operacoes()
