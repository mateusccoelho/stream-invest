import streamlit as st
import pandas as pd

from src.dashboard.formatacao import formatar_dinheiro, formatar_porcentagem


def mostrar_metricas(metricas: pd.DataFrame):
    titulo_metricas = ["Patrimônio", "Retorno", "Retorno (%)", "Quantidade de ativos"]
    cols = st.columns(4)
    cols[0].metric(titulo_metricas[0], formatar_dinheiro(metricas[0]))
    cols[1].metric(titulo_metricas[1], formatar_dinheiro(metricas[1]))
    cols[2].metric(titulo_metricas[2], formatar_porcentagem(metricas[2]))
    cols[3].metric(titulo_metricas[3], metricas[3])
