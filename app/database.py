"""
Banco de dados: SQLAlchemy + SQLite (dev local) ou Postgres (produção).
Define o modelo Expense e a engine compartilhada.
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finbot.db")

# Supabase/Heroku/Render às vezes entregam a URL como "postgres://",
# mas SQLAlchemy moderno exige "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configurações específicas por tipo de banco
if DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False só é válido (e necessário) pra SQLite com múltiplas threads
    connect_args = {"check_same_thread": False}
    engine_kwargs = {"connect_args": connect_args}
else:
    # Postgres: usa pool com pre_ping pra evitar conexões mortas após hibernação do Render
    engine_kwargs = {
        "pool_pre_ping": True,  # testa a conexão antes de usar
        "pool_recycle": 300,    # recicla conexões a cada 5 min
    }

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True, nullable=False)  # telegram user id
    item = Column(String(120), nullable=False)
    category = Column(String(40), nullable=False)
    amount = Column(Float, nullable=False)
    raw_message = Column(String(500))  # mensagem original do usuário
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def init_db():
    """Cria as tabelas se não existirem. Chamado no startup."""
    Base.metadata.create_all(bind=engine)
