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

Os dados de operações são armazenados em um banco de dados SQLite localizado em `dados/investimentos.db`. A atualização dos indicadores e a inicialização do dashboard devem ser disparados por meio do script `start.sh`.

### Migração da planilha

O projeto originalmente usava uma planilha Excel (`dados/Investimentos.xlsx`). Se o banco de dados SQLite ainda não existir e a planilha estiver presente na pasta `dados`, o script `start.sh` executará automaticamente a migração dos dados. A migração também pode ser executada manualmente:

```bash
python -m src.migra_excel_sqlite
```

### Cadastro de operações

Novas operações podem ser cadastradas diretamente pelo dashboard na página **Operações** (aba lateral). Após cadastrar, reinicie o dashboard para que os dados sejam recalculados.

### Banco de dados


O banco de dados é composto por 6 tabelas que serão explicadas detalhadamente a seguir: `aportes_rf`, `resgates_rf`, `transacoes_rv`, `proventos_rv`, `ativos_rv` e `proporcoes`.


#### aportes_rf

Cada linha representa um aporte em um título de renda fixa, com as seguintes colunas:

| Nome            | Tipo de variável | Descrição                                                        | Valores possíveis           |
|-----------------|------------------|------------------------------------------------------------------|-----------------------------|
| id              | int              | Identificador único do aporte (PK)                               | Inteiro sequencial ≥ 1      |
| corretora       | str              | Nome da corretora onde o aporte foi realizado                    | Livre                      |
| emissor         | str              | Nome do emissor do título                                        | Livre                      |
| tipo            | str              | Tipo do título de renda fixa                                     | CDB, LCI, LCA              |
| forma           | str              | Tipo do indexador do título                                      | Pós, Pré                   |
| data_compra     | date             | Data em que o aporte foi realizado                               | AAAA-MM-DD                 |
| data_vencimento | date             | Data de vencimento do título                                     | AAAA-MM-DD                 |
| indexador       | str              | Indexador do título                                              | CDI, Pré, IPCA +           |
| taxa            | float            | Taxa de juros do título                                          | Livre                      |
| valor           | float            | Valor investido no título                                        | Livre                      |
| reserva         | bool             | Flag indicando se é reserva de emergência                        | 0 (False), 1 (True)        |


#### resgates_rf

Cada linha representa um resgate em um título de renda fixa, com as seguintes colunas:

| Nome         | Tipo de variável | Descrição                                                                 | Valores possíveis           |
|--------------|------------------|---------------------------------------------------------------------------|-----------------------------|
| id           | int              | Identificador do título resgatado (FK para aportes_rf)                    | Inteiro sequencial ≥ 1      |
| data_resgate | date             | Data em que o resgate foi realizado                                       | AAAA-MM-DD                  |
| valor        | float            | Valor resgatado, incluindo juros acumulados                               | Livre                       |
| final        | bool             | Flag indicando se o resgate foi total (final) ou parcial                  | 0 (parcial), 1 (total)      |


#### transacoes_rv

Cada linha representa uma transação (compra ou venda) em um ativo de renda variável, com as seguintes colunas:

| Nome         | Tipo de variável | Descrição                                         | Valores possíveis         |
|--------------|------------------|---------------------------------------------------|---------------------------|
| data         | date             | Data da transação                                 | AAAA-MM-DD                |
| codigo       | str              | Código de negociação do ativo                     | Livre                     |
| operacao     | str              | Indica se é compra ou venda                       | C (compra), V (venda)     |
| quantidade   | int              | Quantidade de ativos negociados                   | Inteiro ≥ 1               |
| preco        | float            | Preço unitário do ativo                           | Livre                     |
| corretora    | str              | Nome da corretora                                 | Livre                     |
| taxas        | float            | Taxas associadas à transação                      | Livre                     |


#### proventos_rv

Cada linha representa um provento recebido de um ativo de renda variável, com as seguintes colunas:

| Nome            | Tipo de variável | Descrição                                 | Valores possíveis |
|-----------------|------------------|-------------------------------------------|-------------------|
| data_pagamento  | date             | Data em que o provento foi pago           | AAAA-MM-DD        |
| codigo          | str              | Código de negociação do ativo             | Livre             |
| quantidade      | int              | Quantidade de ativos que geraram provento | Inteiro ≥ 1       |
| valor           | float            | Valor unitário do provento recebido       | Livre             |
| tipo            | str              | Tipo do provento                          | Rendimento        |


#### ativos_rv

Cada linha representa um ativo de renda variável, com as seguintes colunas:

| Nome      | Tipo de variável | Descrição                        | Valores possíveis        |
|-----------|------------------|----------------------------------|--------------------------|
| codigo    | str              | Código de negociação do ativo (PK)| Livre                    |
| tipo      | str              | Tipo do ativo                    | Ação, ETF, FII, FI-Infra |
| benchmark | str              | Benchmark de comparação do ativo | Livre                    |


#### proporcoes

Cada linha representa a proporção alvo de uma classe de ativos na carteira, com as seguintes colunas:

| Nome      | Tipo de variável | Descrição                                         | Valores possíveis                                             |
|-----------|------------------|---------------------------------------------------|---------------------------------------------------------------|
| classe    | str              | Classe de ativos (PK)                             | Títulos CDI, FI-Infra CDI, ETF IMAB, Títulos IPCA+, FI-Infra IMAB, Títulos Pré, Ações Brasil, Ações Mundo |
| proporcao | float            | Proporção alvo da classe de ativos na carteira (%)| 0.0 a 1.0 (percentual)                                        |