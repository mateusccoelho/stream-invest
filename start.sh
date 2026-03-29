#!/bin/bash
export LANG=en_US.UTF-8

python src/atualiza_cotacoes.py
streamlit run "src/dashboard/app.py"