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

**Os valores possíveis para os campos categóricos estão definidos em:** [src/dashboard/constants.py](src/dashboard/constants.py)

#### aportes_rf

Cada linha representa um aporte em um título de renda fixa, com as seguintes colunas:

| Nome            | Tipo de variável | Descrição                                                        |
|-----------------|------------------|------------------------------------------------------------------|
| id              | INTEGER          | Identificador único do aporte (PK)                               |
| corretora       | TEXT             | Nome da corretora onde o aporte foi realizado                    |
| emissor         | TEXT             | Nome do emissor do título                                        |
| tipo            | TEXT             | Tipo do título de renda fixa                                     |
| forma           | TEXT             | Tipo do indexador do título                                      |
| data_compra     | TEXT             | Data em que o aporte foi realizado                               |
| data_vencimento | TEXT             | Data de vencimento do título                                     |
| indexador       | TEXT             | Indexador do título                                              |
| taxa            | REAL             | Taxa de juros do título                                          |
| valor           | REAL             | Valor investido no título                                        |
| reserva         | INTEGER          | Flag indicando se é reserva de emergência                        |


#### resgates_rf

Cada linha representa um resgate em um título de renda fixa, com as seguintes colunas:

| Nome         | Tipo de variável | Descrição                                                                 |
|--------------|------------------|---------------------------------------------------------------------------|
| id           | INTEGER          | Identificador do título resgatado (FK para aportes_rf)                    |
| data_resgate | TEXT             | Data em que o resgate foi realizado                                       |
| valor        | REAL             | Valor resgatado, incluindo juros acumulados                               |
| final        | INTEGER          | Flag indicando se o resgate foi total (final) ou parcial                  |


#### transacoes_rv

Cada linha representa uma transação (compra ou venda) em um ativo de renda variável, com as seguintes colunas:

| Nome         | Tipo de variável | Descrição                                         |
|--------------|------------------|---------------------------------------------------|
| data         | TEXT             | Data da transação                                 |
| codigo       | TEXT             | Código de negociação do ativo                     |
| operacao     | TEXT             | Indica se é compra ou venda                       |
| quantidade   | INTEGER          | Quantidade de ativos negociados                   |
| preco        | REAL             | Preço unitário do ativo                           |
| corretora    | TEXT             | Nome da corretora                                 |
| taxas        | REAL             | Taxas associadas à transação                      |


#### proventos_rv

Cada linha representa um provento recebido de um ativo de renda variável, com as seguintes colunas:

| Nome            | Tipo de variável | Descrição                                 |
|-----------------|------------------|-------------------------------------------|
| data_pagamento  | TEXT             | Data em que o provento foi pago           |
| codigo          | TEXT             | Código de negociação do ativo             |
| quantidade      | INTEGER          | Quantidade de ativos que geraram provento |
| valor           | REAL             | Valor unitário do provento recebido       |
| tipo            | TEXT             | Tipo do provento                          |


#### ativos_rv

Cada linha representa um ativo de renda variável, com as seguintes colunas:

| Nome      | Tipo de variável | Descrição                        |
|-----------|------------------|----------------------------------|
| codigo    | TEXT             | Código de negociação do ativo (PK)|
| tipo      | TEXT             | Tipo do ativo                    |
| benchmark | TEXT             | Benchmark de comparação do ativo |


#### proporcoes

Cada linha representa a proporção alvo de uma classe de ativos na carteira, com as seguintes colunas:

| Nome      | Tipo de variável | Descrição                                         |
|-----------|------------------|---------------------------------------------------|
| classe    | TEXT             | Classe de ativos (PK)                             |
| proporcao | REAL             | Proporção alvo da classe de ativos na carteira (%)|
