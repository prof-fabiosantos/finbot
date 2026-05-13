"""
Camada de serviço: encapsula operações no banco.
Mantém os handlers do bot magros e testáveis.
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from .database import SessionLocal, Expense


def save_expense(user_id: int, item: str, category: str, amount: float, raw: str) -> Expense:
    db = SessionLocal()
    try:
        exp = Expense(
            user_id=user_id,
            item=item,
            category=category,
            amount=amount,
            raw_message=raw,
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp
    finally:
        db.close()


def total_this_month(user_id: int) -> float:
    """Soma todos os gastos do usuário no mês corrente (UTC)."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
        total = (
            db.query(func.sum(Expense.amount))
            .filter(Expense.user_id == user_id, Expense.created_at >= start)
            .scalar()
        )
        return float(total or 0)
    finally:
        db.close()


def total_by_category_month(user_id: int) -> list[tuple[str, float]]:
    """Retorna [(categoria, total), ...] do mês corrente, ordenado por total desc."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
        rows = (
            db.query(Expense.category, func.sum(Expense.amount))
            .filter(Expense.user_id == user_id, Expense.created_at >= start)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
            .all()
        )
        return [(cat, float(total)) for cat, total in rows]
    finally:
        db.close()


def list_recent(user_id: int, limit: int = 10) -> list[Expense]:
    db = SessionLocal()
    try:
        return (
            db.query(Expense)
            .filter(Expense.user_id == user_id)
            .order_by(Expense.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def delete_last(user_id: int) -> Expense | None:
    """Remove o último gasto registrado pelo usuário. Útil pra desfazer erros."""
    db = SessionLocal()
    try:
        last = (
            db.query(Expense)
            .filter(Expense.user_id == user_id)
            .order_by(Expense.created_at.desc())
            .first()
        )
        if last:
            db.delete(last)
            db.commit()
        return last
    finally:
        db.close()
