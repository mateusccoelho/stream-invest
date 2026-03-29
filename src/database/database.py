"""
Módulo de acesso ao banco de dados SQLite.

Centraliza a criação do schema, leitura e escrita de dados
para substituir o uso da planilha Excel.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import date

import pandas as pd
import pandera.pandas as pa

import src.database.schemas as schemas

CAMINHO_DADOS = Path(__file__).resolve().parent.parent.parent / "dados"
CAMINHO_DB = CAMINHO_DADOS / "investimentos.db"


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------


@contextmanager
def conectar():
    """Context manager que retorna uma conexão SQLite."""
    conn = sqlite3.connect(
        str(CAMINHO_DB),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS aportes_rf (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    corretora       TEXT    NOT NULL,
    emissor         TEXT    NOT NULL,
    tipo            TEXT    NOT NULL,
    forma           TEXT    NOT NULL,
    data_compra     TEXT    NOT NULL,  -- YYYY-MM-DD
    data_vencimento TEXT    NOT NULL,  -- YYYY-MM-DD
    indexador       TEXT    NOT NULL,
    taxa            REAL    NOT NULL,
    valor           REAL    NOT NULL,
    reserva         INTEGER NOT NULL DEFAULT 0  -- 0=False, 1=True
);

CREATE TABLE IF NOT EXISTS resgates_rf (
    rowid_          INTEGER PRIMARY KEY AUTOINCREMENT,
    id              INTEGER NOT NULL,
    data_resgate    TEXT    NOT NULL,  -- YYYY-MM-DD
    valor           REAL    NOT NULL,
    final           INTEGER NOT NULL DEFAULT 0,  -- 0=False, 1=True
    FOREIGN KEY (id) REFERENCES aportes_rf(id)
);

CREATE TABLE IF NOT EXISTS transacoes_rv (
    rowid_          INTEGER PRIMARY KEY AUTOINCREMENT,
    data            TEXT    NOT NULL,  -- YYYY-MM-DD
    codigo          TEXT    NOT NULL,
    operacao        TEXT    NOT NULL,
    quantidade      INTEGER NOT NULL,
    preco           REAL    NOT NULL,
    corretora       TEXT    NOT NULL,
    taxas           REAL    NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS proventos_rv (
    rowid_          INTEGER PRIMARY KEY AUTOINCREMENT,
    data_pagamento  TEXT    NOT NULL,  -- YYYY-MM-DD
    codigo          TEXT    NOT NULL,
    quantidade      INTEGER NOT NULL,
    valor           REAL    NOT NULL,
    tipo            TEXT    NOT NULL DEFAULT 'Rendimento'
);

CREATE TABLE IF NOT EXISTS ativos_rv (
    codigo          TEXT PRIMARY KEY,
    tipo            TEXT NOT NULL,
    benchmark       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proporcoes (
    classe          TEXT PRIMARY KEY,
    proporcao       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS cotacoes (
    data            TEXT    NOT NULL,  -- YYYY-MM-DD
    codigo          TEXT    NOT NULL,
    valor           REAL,
    variacao        REAL,
    PRIMARY KEY (data, codigo)
);
"""


def criar_tabelas():
    """Cria as tabelas caso não existam e aplica migrações pendentes."""
    with conectar() as conn:
        conn.executescript(_SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Leitura (retorna DataFrames com nomes de coluna iguais aos da planilha)
# ---------------------------------------------------------------------------


@pa.check_output(schemas.AportesRFSchema)
def ler_aportes_rf() -> pd.DataFrame:
    with conectar() as conn:
        df = pd.read_sql_query(
            "SELECT id, corretora, emissor, tipo, forma, "
            "data_compra, data_vencimento AS data_venc, indexador AS 'index', "
            "taxa, valor, reserva FROM aportes_rf ORDER BY id",
            conn,
        )
    for col in ["data_compra", "data_venc"]:
        df[col] = pd.to_datetime(df[col]).dt.date
    df["reserva"] = df["reserva"].astype(bool)
    return df


@pa.check_output(schemas.ResgatesRFSchema)
def ler_resgates_rf() -> pd.DataFrame:
    with conectar() as conn:
        df = pd.read_sql_query(
            "SELECT id, data_resgate, valor, final "
            "FROM resgates_rf ORDER BY data_resgate",
            conn,
        )
    df["data_resgate"] = pd.to_datetime(df["data_resgate"]).dt.date
    df["final"] = df["final"].astype(bool)
    return df


@pa.check_output(schemas.TransacoesRVSchema)
def ler_transacoes_rv() -> pd.DataFrame:
    with conectar() as conn:
        df = pd.read_sql_query(
            "SELECT data, codigo, operacao AS tipo, quantidade AS qtd, "
            "preco, corretora, taxas FROM transacoes_rv ORDER BY codigo, data",
            conn,
        )
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df


@pa.check_output(schemas.ProventosRVSchema)
def ler_proventos_rv() -> pd.DataFrame:
    with conectar() as conn:
        df = pd.read_sql_query(
            "SELECT data_pagamento AS dt_pag, codigo, quantidade AS qtd, "
            "valor, tipo FROM proventos_rv ORDER BY data_pagamento DESC, codigo DESC",
            conn,
        )
    df["dt_pag"] = pd.to_datetime(df["dt_pag"]).dt.date
    return df


@pa.check_output(schemas.AtivosRVSchema)
def ler_ativos_rv() -> pd.DataFrame:
    with conectar() as conn:
        df = pd.read_sql_query(
            "SELECT codigo, tipo AS tipo_ativo, benchmark AS bench "
            "FROM ativos_rv ORDER BY codigo",
            conn,
        )
    return df


@pa.check_output(schemas.ProporcoesSchema)
def ler_proporcoes() -> pd.DataFrame:
    with conectar() as conn:
        df = pd.read_sql_query("SELECT classe, proporcao FROM proporcoes", conn)
    return df


@pa.check_output(schemas.CotacoesSchema)
def ler_cotacoes() -> pd.DataFrame:
    """Retorna o histórico completo de cotações / indicadores."""
    with conectar() as conn:
        df = pd.read_sql_query(
            "SELECT data, codigo, valor, variacao FROM cotacoes "
            "ORDER BY codigo, data",
            conn,
        )
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df


def ler_datas_cotacoes(codigo: str, data_inicio: date | None = None) -> list[date]:
    """Lê cotações de um indicador, opcionalmente a partir de uma data."""

    with conectar() as conn:
        if data_inicio:
            df = pd.read_sql_query(
                "SELECT DISTINCT data FROM cotacoes "
                "WHERE codigo = ? AND data >= ? ORDER BY data",
                conn,
                params=(codigo, str(data_inicio)),
            )
        else:
            df = pd.read_sql_query(
                "SELECT DISTINCT data FROM cotacoes " "WHERE codigo = ? ORDER BY data",
                conn,
                params=(codigo,),
            )

    if not df.empty:
        return pd.to_datetime(df["data"]).dt.date.tolist()

    return []


# ---------------------------------------------------------------------------
# Escrita – inserções unitárias (para o formulário do dashboard)
# ---------------------------------------------------------------------------


def inserir_aporte_rf(
    corretora: str,
    emissor: str,
    tipo: str,
    forma: str,
    data_compra: str,
    data_vencimento: str,
    indexador: str,
    taxa: float,
    valor: float,
    reserva: bool,
) -> int:
    """Insere um aporte RF e retorna o ID gerado."""
    with conectar() as conn:
        cursor = conn.execute(
            "INSERT INTO aportes_rf "
            "(corretora, emissor, tipo, forma, data_compra, data_vencimento, "
            "indexador, taxa, valor, reserva) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                corretora,
                emissor,
                tipo,
                forma,
                str(data_compra),
                str(data_vencimento),
                indexador,
                taxa,
                valor,
                int(reserva),
            ),
        )
        return cursor.lastrowid


def inserir_resgate_rf(
    id_aporte: int,
    data_resgate: str,
    valor: float,
    final: bool,
):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO resgates_rf (id, data_resgate, valor, final) "
            "VALUES (?, ?, ?, ?)",
            (id_aporte, str(data_resgate), valor, int(final)),
        )


def inserir_transacao_rv(
    data: str,
    codigo: str,
    operacao: str,
    quantidade: int,
    preco: float,
    corretora: str,
    taxas: float,
):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO transacoes_rv "
            "(data, codigo, operacao, quantidade, preco, corretora, taxas) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(data), codigo, operacao, quantidade, preco, corretora, taxas),
        )


def inserir_provento_rv(
    data_pagamento: str,
    codigo: str,
    quantidade: int,
    valor: float,
    tipo: str = "Rendimento",
):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO proventos_rv "
            "(data_pagamento, codigo, quantidade, valor, tipo) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(data_pagamento), codigo, quantidade, valor, tipo),
        )


def inserir_ativo_rv(
    codigo: str,
    tipo: str,
    benchmark: str,
):
    with conectar() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ativos_rv (codigo, tipo, benchmark) "
            "VALUES (?, ?, ?)",
            (codigo, tipo, benchmark),
        )


def atualizar_proporcoes(proporcoes: dict[str, float]):
    """Atualiza as proporções existentes no banco."""

    with conectar() as conn:
        for classe, proporcao in proporcoes.items():
            conn.execute(
                "UPDATE proporcoes SET proporcao = ? WHERE classe = ?",
                (proporcao, classe),
            )


def inserir_cotacao(
    data: str,
    codigo: str,
    valor: float | None,
    variacao: float | None,
):
    """Insere ou atualiza uma linha na tabela cotacoes."""
    with conectar() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cotacoes (data, codigo, valor, variacao) "
            "VALUES (?, ?, ?, ?)",
            (str(data), codigo, valor, variacao),
        )
