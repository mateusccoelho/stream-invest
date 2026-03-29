from pathlib import Path
import sys

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

st.set_page_config(
    page_title="Stream-invest",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded",
)

patrimonio = st.Page(
    str(BASE_DIR / "pages" / "1_Patrimônio.py"),
    title="Patrimônio",
    icon="💼",
    default=True,
)
rebalanceamento = st.Page(
    str(BASE_DIR / "pages" / "2_Rebalanceamento.py"),
    title="Rebalanceamento",
    icon="⚖️",
)
renda_fixa = st.Page(
    str(BASE_DIR / "pages" / "3_Renda_Fixa.py"),
    title="Renda Fixa",
    icon="🏦",
)
renda_variavel = st.Page(
    str(BASE_DIR / "pages" / "4_Renda_Variável.py"),
    title="Renda Variável",
    icon="📈",
)
proventos = st.Page(
    str(BASE_DIR / "pages" / "5_Proventos.py"),
    title="Proventos",
    icon="💸",
)
cadastro = st.Page(
    str(BASE_DIR / "pages" / "6_Cadastro.py"),
    title="Cadastro",
    icon="✏️",
)

navigation = st.navigation(
    [patrimonio, rebalanceamento, renda_fixa, renda_variavel, proventos, cadastro],
    position="hidden",
)

with st.sidebar:
    st.markdown("## 💰 Stream-invest")
    st.caption("Painel de acompanhamento de investimentos")
    st.space(size="xxsmall")

    st.page_link(patrimonio)
    st.page_link(rebalanceamento)
    st.page_link(renda_fixa)
    st.page_link(renda_variavel)
    st.page_link(proventos)
    st.page_link(cadastro)

navigation.run()
