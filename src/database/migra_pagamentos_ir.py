"""
Migração: cria a tabela pagamentos_ir no banco SQLite existente.

Uso:
    python -m src.database.migra_pagamentos_ir

Não remove nem altera tabelas existentes — apenas adiciona a nova tabela.
"""

from src.database.database import conectar

_SQL = """
CREATE TABLE IF NOT EXISTS pagamentos_ir (
    rowid_          INTEGER PRIMARY KEY AUTOINCREMENT,
    data_pagamento  TEXT    NOT NULL,  -- YYYY-MM-DD  (data em que o DARF foi pago)
    ano_ref         INTEGER NOT NULL,  -- ano-calendário de referência
    mes_ref         INTEGER NOT NULL,  -- mês de referência (1-12)
    valor           REAL    NOT NULL   -- valor pago em R$
);
"""


def migrar():
    with conectar() as conn:
        conn.executescript(_SQL)
    print("Tabela 'pagamentos_ir' criada (ou já existia).")


if __name__ == "__main__":
    migrar()
