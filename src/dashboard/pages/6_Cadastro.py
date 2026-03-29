"""
Página de cadastro de novas operações do dashboard.
"""

import sys

sys.path.append("..")

import pandas as pd
import streamlit as st

from src.database import (
    inserir_aporte_rf,
    inserir_resgate_rf,
    inserir_transacao_rv,
    inserir_provento_rv,
    inserir_ativo_rv,
    atualizar_proporcoes,
)
from src.dashboard.dados import carregar_dados
from src.dashboard.formatacao import formatar_dinheiro


def limpar_cache():
    st.cache_data.clear()
    st.cache_resource.clear()


def _tab_aporte_rf(aportes_rf: pd.DataFrame):
    """Aba para cadastro de novos aportes de renda fixa."""

    corretoras_rf = sorted(aportes_rf["corretora"].dropna().unique().tolist())
    emissores_rf = sorted(aportes_rf["emissor"].dropna().unique().tolist())
    tipos_rf = sorted(aportes_rf["tipo"].dropna().unique().tolist())
    formas_rf = sorted(aportes_rf["forma"].dropna().unique().tolist())
    indexadores_rf = sorted(aportes_rf["index"].dropna().unique().tolist())

    with st.form("form_aporte_rf", clear_on_submit=True):
        cols = st.columns(3)

        corretora = cols[0].selectbox(
            "Corretora", corretoras_rf, index=None, accept_new_options=True
        )
        emissor = cols[1].selectbox(
            "Emissor", emissores_rf, index=None, accept_new_options=True
        )
        tipo_rf = cols[2].selectbox(
            "Tipo", tipos_rf, index=None, accept_new_options=True
        )

        cols2 = st.columns(3)
        forma = cols2[0].selectbox(
            "Forma", formas_rf, index=None, accept_new_options=True
        )
        indexador = cols2[1].selectbox(
            "Indexador", indexadores_rf, index=None, accept_new_options=True
        )
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
        submitted = st.form_submit_button("💾 Cadastrar aporte", width="stretch")

    if not submitted:
        return

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
        st.error("Preencha todos os campos obrigatórios.")
        return

    if data_vencimento <= data_compra:
        st.error("Data de vencimento deve ser posterior à data de compra.")
        return

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


def _tab_resgate_rf(aportes_rf: pd.DataFrame, resgates_rf: pd.DataFrame):
    """Aba para cadastro de resgates de renda fixa."""

    ids_com_resgate_final = resgates_rf.loc[resgates_rf["final"], "id"].tolist()
    aportes_ativos = aportes_rf.loc[~aportes_rf["id"].isin(ids_com_resgate_final), :]

    if aportes_ativos.empty:
        st.warning("Não há aportes RF ativos para resgatar.")
        return

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
        id_resgate = cols[0].selectbox(
            "ID do aporte", sorted(aportes_ativos["id"].tolist()), index=None
        )
        data_resgate = cols[1].date_input("Data do resgate", value=None)
        valor_resgate = cols[2].number_input(
            "Valor resgatado (R$)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            value=None,
        )
        final = st.checkbox("Resgate total (final)")
        submitted = st.form_submit_button("💾 Cadastrar resgate", width="stretch")

    if not submitted:
        return

    required = [id_resgate, data_resgate, valor_resgate]
    if any(
        x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
        for x in required
    ):
        st.error("Preencha todos os campos obrigatórios.")
        return

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


def _tab_transacao_rv(ativos_rv: pd.DataFrame, transacoes_rv: pd.DataFrame):
    """Aba para cadastro de transações de renda variável."""

    codigos = sorted(ativos_rv["codigo"].tolist())
    corretoras_rv = sorted(transacoes_rv["corretora"].dropna().unique().tolist())

    with st.form("form_transacao_rv", clear_on_submit=True):
        cols = st.columns(4)
        data_trans = cols[0].date_input("Data", value=None)
        codigo_trans = cols[1].selectbox("Código do ativo", codigos, index=None)
        operacao = cols[2].selectbox(
            "Operação",
            ["C", "V"],
            index=None,
            format_func=lambda x: "Compra" if x == "C" else "Venda",
        )
        corretora_rv = cols[3].selectbox(
            "Corretora", corretoras_rv, index=None, accept_new_options=True
        )

        cols2 = st.columns(3)
        qtd_trans = cols2[0].number_input("Quantidade", min_value=0, step=1, value=None)
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

        submitted = st.form_submit_button("💾 Cadastrar transação", width="stretch")

    if not submitted:
        return

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
        return

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
        f"de **{qtd_trans}x {codigo_trans}** "
        f"({formatar_dinheiro(valor_total)}) cadastrada!"
    )
    limpar_cache()


def _tab_provento_rv(ativos_rv: pd.DataFrame, proventos: pd.DataFrame):
    """Aba para cadastro de proventos de renda variável."""

    codigos = sorted(ativos_rv["codigo"].tolist())
    tipos_prov = sorted(proventos["tipo"].dropna().unique().tolist())

    with st.form("form_provento_rv", clear_on_submit=True):
        cols = st.columns(4)
        data_prov = cols[0].date_input("Data de pagamento", value=None)
        codigo_prov = cols[1].selectbox("Código do ativo", codigos, index=None)
        qtd_prov = cols[2].number_input("Quantidade", min_value=0, step=1, value=None)
        valor_prov = cols[3].number_input(
            "Valor unitário (R$)",
            min_value=0.0,
            step=0.0001,
            format="%.4f",
            value=None,
        )

        tipo_prov = st.selectbox(
            "Tipo", tipos_prov, index=None, accept_new_options=True
        )
        submitted = st.form_submit_button("💾 Cadastrar provento", width="stretch")

    if not submitted:
        return

    required = [data_prov, codigo_prov, qtd_prov, valor_prov, tipo_prov]
    if any(
        x is None or x == "" or (isinstance(x, (int, float)) and x <= 0)
        for x in required
    ):
        st.error("Preencha todos os campos obrigatórios.")
        return

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


def _tab_ativo_rv(ativos_rv: pd.DataFrame):
    """Aba para cadastro/atualização de ativos de renda variável."""

    tipos_ativo_rv = sorted(ativos_rv["tipo_ativo"].dropna().unique().tolist())
    benchmarks = sorted(ativos_rv["bench"].dropna().unique().tolist())

    with st.form("form_ativo_rv", clear_on_submit=True):
        cols = st.columns(3)
        codigo_ativo = cols[0].text_input("Código do ativo")
        tipo_ativo = cols[1].selectbox(
            "Tipo", tipos_ativo_rv, index=None, accept_new_options=True
        )
        benchmark = cols[2].selectbox(
            "Benchmark", benchmarks, index=None, accept_new_options=True
        )

        submitted = st.form_submit_button("💾 Cadastrar ativo", width="stretch")

    if not submitted:
        return

    required = [codigo_ativo, tipo_ativo, benchmark]
    if any(x is None or x == "" for x in required):
        st.error("Preencha todos os campos obrigatórios.")
        return

    inserir_ativo_rv(
        codigo=codigo_ativo.upper(),
        tipo=tipo_ativo,
        benchmark=benchmark,
    )
    st.success(f"Ativo **{codigo_ativo.upper()}** cadastrado/atualizado!")
    limpar_cache()


def _tab_proporcoes(proporcoes: pd.DataFrame):
    """Aba para edição de proporções alvo da carteira."""

    st.caption("Edite os valores de proporção e clique em salvar.")

    editado = st.data_editor(
        proporcoes,
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
    submitted = st.button("💾 Salvar proporções", width="stretch")

    if not submitted:
        return

    novos_valores = dict(zip(editado["classe"], editado["proporcao"]))
    atualizar_proporcoes(novos_valores)
    st.success("Proporções atualizadas!")
    limpar_cache()


def pagina_operacoes(
    aportes_rf: pd.DataFrame,
    ativos_rv: pd.DataFrame,
    resgates_rf: pd.DataFrame,
    proporcoes: pd.DataFrame,
    transacoes_rv: pd.DataFrame,
    proventos: pd.DataFrame,
):
    """Página principal de cadastro com abas para cada funcionalidade."""

    st.markdown("# Cadastro de Operações")

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

    with tabs[0]:
        _tab_aporte_rf(aportes_rf)

    with tabs[1]:
        _tab_resgate_rf(aportes_rf, resgates_rf)

    with tabs[2]:
        _tab_transacao_rv(ativos_rv, transacoes_rv)

    with tabs[3]:
        _tab_provento_rv(ativos_rv, proventos)

    with tabs[4]:
        _tab_ativo_rv(ativos_rv)

    with tabs[5]:
        _tab_proporcoes(proporcoes)


st.set_page_config(
    page_title="Cadastro de Operações",
    page_icon=":pencil:",
    layout="wide",
    initial_sidebar_state="expanded",
)

dados = carregar_dados()
pagina_operacoes(
    aportes_rf=dados["aportes_rf"],
    ativos_rv=dados["ativos_rv"],
    resgates_rf=dados["resgates_rf"],
    proporcoes=dados["proporcoes"],
    transacoes_rv=dados["transacoes_rv"],
    proventos=dados["proventos"],
)
