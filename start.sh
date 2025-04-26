#!/bin/bash
export LANG=en_US.UTF-8


python3 src/atualiza_historico.py
cd src/dashboard
streamlit run "1_Patrimônio.py"