"""
Banco de dados: SQLAlchemy + SQLite.
Define o modelo Expense e a engine compartilhada.
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finbot.db")

# check_same_thread=False é necessário porque o bot usa múltiplas threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
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
