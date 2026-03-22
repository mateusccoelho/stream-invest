# Stream-invest

Este projeto é uma interface web feita com o framework [Streamlit](https://streamlit.io/) para monitorar e rebalancear meus investimentos. Ela foi baseada no serviço *status-invest* da Suno, porém mais simplificada e personalizada para as visualizações que eu gostaria de ter. 

## Interface

Atualmente o aplicativo contém 5 páginas:

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

## Dados

O processo de atualização ainda é manual. Os dados são preenchidos em uma planilha no Google Sheets (drive) e devem ser manualmente baixados em formato Excel (.xlsx) para a máquina local. O diretório deve ser `dados`, contido neste repositório. Depois, a atualização dos indicadores e a inicialização do dashboard devem ser disparados por meio do script `start.sh`.

### Planilha

A planilha é composta por 6 abas que serão explicadas detalhadamente a seguir: `Aportes RF`, `Resgates RF`, `Transações RV`, `Proventos RV`, `Ativos RV` e `Proporções`.


#### Aportes RF

Cada linha representa um aporte em um título de renda fixa, com as seguintes colunas:

| Nome           | Tipo de variável | Descrição                                                        | Valores possíveis           |
|----------------|------------------|------------------------------------------------------------------|-----------------------------|
| ID             | int              | Identificador único do aporte                                    | Inteiro sequencial ≥ 1      |
| Corretora      | str              | Nome da corretora onde o aporte foi realizado                    | Livre                      |
| Emissor        | str              | Nome do emissor do título                                        | Livre                      |
| Tipo           | str              | Tipo do título de renda fixa                                     | CDB, LCI, LCA              |
| Forma          | str              | Tipo do indexador do título                                      | Pós, Pré                   |
| Data compra    | date             | Data em que o aporte foi realizado                               | AAAA-MM-DD                 |
| Data vencimento| date             | Data de vencimento do título                                     | AAAA-MM-DD                 |
| Indexador      | str              | Indexador do título                                              | CDI, Pré, IPCA +           |
| Taxa           | float            | Taxa de juros do título                                          | Livre                      |
| Valor          | float            | Valor investido no título                                        | Livre                      |
| Reserva        | bool             | Flag indicando se é reserva de emergência                        | True, False                |


#### Resgates RF

Cada linha representa um resgate em um título de renda fixa, com as seguintes colunas:

| Nome         | Tipo de variável | Descrição                                                                 | Valores possíveis           |
|--------------|------------------|---------------------------------------------------------------------------|-----------------------------|
| ID           | int              | Identificador do título resgatado (igual ao ID do aporte correspondente)   | Inteiro sequencial ≥ 1      |
| Data resgate | date             | Data em que o resgate foi realizado                                       | AAAA-MM-DD                  |
| Valor        | float            | Valor resgatado, incluindo juros acumulados                               | Livre                       |
| Final        | bool             | Flag indicando se o resgate foi total (final) ou parcial                  | True (total), False (parcial)|


#### Transações RV

Cada linha representa uma transação (compra ou venda) em um ativo de renda variável, com as seguintes colunas:

| Nome         | Tipo de variável | Descrição                                         | Valores possíveis         |
|--------------|------------------|---------------------------------------------------|---------------------------|
| Data         | date             | Data da transação                                 | AAAA-MM-DD                |
| Código       | str              | Código de negociação do ativo                     | Livre                     |
| Operação C/V | str              | Indica se é compra ou venda                       | C (compra), V (venda)     |
| Quantidade   | int              | Quantidade de ativos negociados                   | Inteiro ≥ 1               |
| Preço        | float            | Preço unitário do ativo                           | Livre                     |
| Corretora    | str              | Nome da corretora                                 | Livre                     |
| Taxas        | float            | Taxas associadas à transação                      | Livre                     |


#### Proventos RV

Cada linha representa um provento recebido de um ativo de renda variável, com as seguintes colunas:

| Nome           | Tipo de variável | Descrição                                 | Valores possíveis |
|----------------|------------------|-------------------------------------------|-------------------|
| Data pagamento | date             | Data em que o provento foi pago           | AAAA-MM-DD        |
| Código         | str              | Código de negociação do ativo             | Livre             |
| Quantidade     | int              | Quantidade de ativos que geraram provento | Inteiro ≥ 1       |
| Valor          | float            | Valor unitário do provento recebido       | Livre             |
| Tipo           | str              | Tipo do provento                          | Rendimento        |


#### Ativos RV

Cada linha representa um ativo de renda variável, com as seguintes colunas:

| Nome      | Tipo de variável | Descrição                        | Valores possíveis      |
|-----------|------------------|----------------------------------|------------------------|
| Código    | str              | Código de negociação do ativo    | Livre                  |
| Tipo      | str              | Tipo do ativo                    | Ação, ETF, FII         |
| Benchmark | str              | Benchmark de comparação do ativo | Livre                  |


#### Proporções

Cada linha representa a proporção alvo de uma classe de ativos na carteira, com as seguintes colunas:

| Nome      | Tipo de variável | Descrição                                         | Valores possíveis                                             |
|-----------|------------------|---------------------------------------------------|---------------------------------------------------------------|
| Classe    | str              | Classe de ativos                                  | Títulos CDI, FI-Infra CDI, ETF IMAB, Títulos IPCA+, FI-Infra IMAB, Títulos Pré, Ações Brasil, Ações Mundo |
| Proporção | float            | Proporção alvo da classe de ativos na carteira (%)| 0.0 a 1.0 (percentual)                                        |