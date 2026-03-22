#!/bin/bash
export LANG=en_US.UTF-8

# Migra dados do Excel para SQLite (só roda se o banco não existir)
if [ ! -f "dados/investimentos.db" ]; then
    echo "Banco de dados não encontrado. Migrando dados do Excel..."
    python -m src.migra_excel_sqlite
fi

python src/atualiza_historico.py
cd src/dashboard
streamlit run "1_Patrimônio.py"