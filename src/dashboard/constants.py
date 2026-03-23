# Valores possíveis para os campos categóricos do banco de dados.

from src.database import listar_classes_ativos

TIPOS_RF = ["CDB", "LCI", "LCA"]
FORMAS_RF = ["Pós", "Pré"]
INDEXADORES_RF = ["CDI", "Pré", "IPCA +"]
OPERACOES_RV = ["C", "V"]
TIPOS_ATIVO_RV = ["ETF", "FI-Infra"]
TIPOS_PROVENTO_RV = ["Rendimento"]

CATEGORIAS_ATIVOS = listar_classes_ativos()
