"""
Script de migração: converte os dados da planilha Excel para o banco SQLite.

Uso:
    python src/migra_excel_sqlite.py

O banco será criado em dados/investimentos.db.
A planilha Excel original não é removida.
"""

import pandas as pd

from src.database import (
    CAMINHO_DB,
    CAMINHO_DADOS,
    criar_tabelas,
    conectar,
)

CAMINHO_EXCEL = CAMINHO_DADOS / "Investimentos.xlsx"


def migrar():
    if not CAMINHO_EXCEL.exists():
        print(f"Planilha não encontrada: {CAMINHO_EXCEL}")
        return

    # Remove banco antigo, se existir, para migrar do zero
    if CAMINHO_DB.exists():
        CAMINHO_DB.unlink()
        print("Banco antigo removido.")

    criar_tabelas()
    print("Tabelas criadas.")

    excel = pd.read_excel(CAMINHO_EXCEL, sheet_name=None, engine="openpyxl")

    # --- Aportes RF ---
    df = excel["Aportes RF"]
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO aportes_rf "
                "(id, corretora, emissor, tipo, forma, data_compra, "
                "data_vencimento, indexador, taxa, valor, reserva) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    int(row["ID"]),
                    str(row["Corretora"]),
                    str(row["Emissor"]),
                    str(row["Tipo"]),
                    str(row["Forma"]),
                    str(pd.Timestamp(row["Data compra"]).date()),
                    str(pd.Timestamp(row["Data vencimento"]).date()),
                    str(row["Indexador"]),
                    float(row["Taxa"]),
                    float(row["Valor"]),
                    int(bool(row["Reserva"])),
                ),
            )
    print(f"  Aportes RF: {len(df)} registros migrados.")

    # --- Resgates RF ---
    df = excel["Resgates RF"]
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO resgates_rf (id, data_resgate, valor, final) "
                "VALUES (?, ?, ?, ?)",
                (
                    int(row["ID"]),
                    str(pd.Timestamp(row["Data resgate"]).date()),
                    float(row["Valor"]),
                    int(bool(row["Final"])),
                ),
            )
    print(f"  Resgates RF: {len(df)} registros migrados.")

    # --- Transações RV ---
    df = excel["Transações RV"]
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO transacoes_rv "
                "(data, codigo, operacao, quantidade, preco, corretora, taxas) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(pd.Timestamp(row["Data"]).date()),
                    str(row["Código"]),
                    str(row["Operação C/V"]),
                    int(row["Quantidade"]),
                    float(row["Preço"]),
                    str(row["Corretora"]),
                    float(row["Taxas"]),
                ),
            )
    print(f"  Transações RV: {len(df)} registros migrados.")

    # --- Proventos RV ---
    df = excel["Proventos RV"]
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO proventos_rv "
                "(data_pagamento, codigo, quantidade, valor, tipo) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    str(pd.Timestamp(row["Data pagamento"]).date()),
                    str(row["Código"]),
                    int(row["Quantidade"]),
                    float(row["Valor"]),
                    str(row["Tipo"]),
                ),
            )
    print(f"  Proventos RV: {len(df)} registros migrados.")

    # --- Ativos RV ---
    df = excel["Ativos RV"]
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO ativos_rv (codigo, tipo, benchmark) " "VALUES (?, ?, ?)",
                (
                    str(row["Código"]),
                    str(row["Tipo"]),
                    str(row["Benchmark"]),
                ),
            )
    print(f"  Ativos RV: {len(df)} registros migrados.")

    # --- Proporções ---
    df = excel["Proporções"]
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO proporcoes (classe, proporcao) VALUES (?, ?)",
                (
                    str(row["Classe"]),
                    float(row["Proporção"]),
                ),
            )
    print(f"  Proporções: {len(df)} registros migrados.")

    print(f"\nMigração concluída! Banco de dados: {CAMINHO_DB}")


if __name__ == "__main__":
    migrar()
