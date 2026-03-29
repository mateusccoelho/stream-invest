#!/bin/bash
export LANG=en_US.UTF-8

python src/atualiza_cotacoes.py
cd src/dashboard
streamlit run "1_Patrimônio.py"