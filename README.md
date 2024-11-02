# Stream-invest

Este projeto é uma interface web feita com o framework [Streamlit](https://streamlit.io/) para monitorar e rebalancear meus investimentos. 

Ela foi baseada no serviço *status-invest* da Suno, porém mais simplificada e personalizada para as visualizações que eu gostaria de ter. Contém 5 páginas:

1. Patrimônio
    - Gráficos de evolução do patrimônio e movimentações na carteira.
    - Posição da carteira no momento por tipo de ativo: ETF, títulos de renda fixa e FI-Infra.
2. Rebalanceamento
    - Tabela com o saldo de cada classe de investimentos e o quanto é necessário investir em cada um.
    - Widgets que permitem fazer simulações de aportes geral ou em alguma classe específica, para ver como ficaria um rebalanceamento futuro.
3. Renda fixa
    - Tabela da posição da carteira, com indicadores de retorno.
    - Tabela que detalha o valor investido por faixa de prazo, junto com a taxa média e a taxa alvo para novos investimentos. Somente disponível para título com indexador CDI simples.
    - Gráfico da exposição por emissor. Útil para avaliar cobertura pelo FGI.
    - Gráfico de evolução do saldo de um título específico à escolha do usuário.
4. Renda variável
    - Tabela da posição da carteira, com indicadores de retorno.
    - Tabela e indicadores de transações relativas a um ativo específico à escolha do usuário.
5. Proventos
    - Gráfico de recebimentos mensais.
    - Tabela com um descritivo histórico dos recebimentos por ativo.
    - Tabela com os detalhes de cada rendimento recebido.

O processo de atualização ainda é manual. Os dados são preenchidos em uma planilha no Google Sheets (drive) e devem ser manualmente baixados em formato Excel (.xlsx) para a máquina local. O diretório deve ser `dados`, contido neste repositório. Depois, a atualização dos indicadores e a inicialização do dashboard devem ser disparados por meio do script `start.bat`.
