import os

from sqlalchemy import (
    Column,
    Integer,
    Float,
    Date,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()
CURRENT_DIT = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{CURRENT_DIT}/investimentos.db"


class TransacoesRV(Base):
    __tablename__ = "TransacoesRV"

    data = Column(Date, primary_key=True)
    codigo = Column(String, primary_key=True)
    quantidade = Column(Integer)
    preco = Column(Float, primary_key=True)
    tipo = Column(String, primary_key=True)
    corretora = Column(String)
    taxa = Column(Float)

    def __repr__(self) -> str:
        return (
            f"<TransacoesRV(data='{self.data}', codigo={self.codigo}, "
            f"quantidade={self.quantidade}, preco={self.preco}, "
            f"tipo='{self.tipo}', corretora='{self.corretora}', taxa={self.taxa})>"
        )


class CarteiraRV(Base):
    __tablename__ = "CarteiraRV"

    codigo = Column(String, primary_key=True)
    data_atualizacao = Column(Date)
    quantidade = Column(Integer)
    patrimonio = Column(Float)
    preco_medio = Column(Float)
    rendimento_total = Column(Float)
    rendimento_hoje = Column(Float)
    status = Column(Integer)

    def __repr__(self) -> str:
        return (
            f"<CarteiraRV(codigo={self.codigo}, data_atualizacao='{self.data_atualizacao}', "
            f"quantidade={self.quantidade}, patrimonio={self.patrimonio}, "
            f"preco_medio={self.preco_medio}, rendimento_total={self.rendimento_total}, "
            f"rendimento_hoje={self.rendimento_hoje}, status={self.status})>"
        )


class Cotacoes(Base):
    __tablename__ = "Cotacoes"

    data = Column(Date, primary_key=True)
    codigo = Column(String, primary_key=True)
    valor = Column(Float)
    variacao = Column(Float)

    def __repr__(self) -> str:
        return (
            f"<Cotacoes(data='{self.data}', codigo={self.codigo}, "
            f"valor={self.valor}, variacao={self.variacao})>"
        )


class PatrimonioRV(Base):
    __tablename__ = "PatrimonioRV"

    data = Column(Date, primary_key=True)
    codigo = Column(String, primary_key=True)
    preco_medio = Column(Float)
    quantidade = Column(Integer)
    patrimonio = Column(Float)
    rendimento = Column(Float)

    def __repr__(self) -> str:
        return (
            f"<PatrimonioRV(data='{self.data}', codigo={self.codigo}, "
            f"preco_medio={self.preco_medio}, quantidade={self.quantidade}, "
            f"patrimonio={self.patrimonio}, rendimento={self.rendimento})>"
        )


class ProventosRV(Base):
    __tablename__ = "ProventosRV"

    data_pagamento = Column(Date, primary_key=True)
    codigo = Column(String, primary_key=True)
    quantidade = Column(Integer)
    valor = Column(Float, primary_key=True)
    tipo = Column(String)

    def __repr__(self) -> str:
        return (
            f"<ProventosRV(data_pagamento='{self.data_pagamento}', codigo={self.codigo}, "
            f"quantidade={self.quantidade}, valor={self.valor}, "
            f"tipo='{self.tipo}')>"
        )


class AtivosRV(Base):
    __tablename__ = "AtivosRV"

    codigo = Column(String, primary_key=True)
    tipo = Column(String)
    benchmark = Column(String)

    def __repr__(self) -> str:
        return (
            f"<AtivosRV(codigo={self.codigo}, tipo='{self.tipo}', "
            f"benchmark='{self.benchmark}')>"
        )


class AportesRendaFixa(Base):
    __tablename__ = "AportesRendaFixa"

    id_titulo = Column(Integer, primary_key=True, autoincrement=True)
    corretora = Column(String)
    emissor = Column(String)
    tipo = Column(String)
    forma = Column(String)
    indexador = Column(String)
    data_compra = Column(Date)
    data_vencimento = Column(Date)
    taxa = Column(Float)
    valor_aplicado = Column(Float)

    __table_args__ = (
        UniqueConstraint(
            "corretora",
            "emissor",
            "tipo",
            "forma",
            "indexador",
            "data_compra",
            "data_vencimento",
            "taxa",
            "valor_aplicado",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AportesRendaFixa(id_titulo={self.id_titulo}, corretora='{self.corretora}', "
            f"emissor='{self.emissor}', "
            f"tipo='{self.tipo}', forma='{self.forma}', indexador='{self.indexador}', "
            f"data_compra='{self.data_compra}', data_vencimento='{self.data_vencimento}', "
            f"taxa={self.taxa}, valor_aplicado={self.valor_aplicado})>"
        )


class CarteiraRF(Base):
    __tablename__ = "CarteiraRF"

    id_titulo = Column(Integer, primary_key=True)
    data_atualizacao = Column(Date)
    saldo = Column(Float)
    resgates = Column(Float)
    rendimentos_bruto = Column(Float)
    status = Column(Integer)

    def __repr__(self) -> str:
        return (
            f"<CarteiraRF(id_titulo={self.id_titulo}, data_atualizacao='{self.data_atualizacao}', "
            f"saldo={self.saldo}, resgates={self.resgates}, rendimentos_bruto={self.rendimentos_bruto}, "
            f"status={self.status})>"
        )


class PatrimonioRF(Base):
    __tablename__ = "PatrimonioRF"

    data = Column(Date, primary_key=True)
    id_titulo = Column(Integer, primary_key=True)
    valor = Column(Float)
    rendimento = Column(Float)
    taxa = Column(Float)

    def __repr__(self) -> str:
        return (
            f"<PatrimonioRF(data='{self.data}', id_titulo={self.idTitulo}, "
            f"valor={self.valor}, rendimento={self.rendimento}, taxa={self.taxa})>"
        )


class ResgatesRF(Base):
    __tablename__ = "ResgatesRF"

    id_titulo = Column(Integer, primary_key=True)
    data = Column(Date, primary_key=True)
    valor = Column(Float)

    def __repr__(self) -> str:
        return (
            f"<CarteiraRF(id_titulo={self.id_titulo}, data='{self.data}', "
            f"valor={self.valor})>"
        )


engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
