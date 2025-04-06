import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ExpenseModel, BudgetModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/expensedb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()