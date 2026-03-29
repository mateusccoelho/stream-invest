#!/bin/bash
export LANG=en_US.UTF-8

# Assugura que os scripts Python sejam executados a partir 
# do diretório onde este script está localizado
cd "$(dirname "$0")"

# Roda o script como módulo para garantir que os caminhos
# relativos funcionem corretamente
python -m src.cotacoes.atualiza_cotacoes

streamlit run "src/dashboard/app.py"