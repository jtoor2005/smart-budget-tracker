from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import random
from sqlalchemy.orm import Session
from database import get_db
from models import ExpenseModel, BudgetModel

# Import budget endpoints
import budget_endpoints

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (replace with specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define expense model
class Expense(BaseModel):
    description: str
    amount: float
    category: Optional[str] = None

class ExpenseInDB(Expense):
    id: int

# Include budget router
app.include_router(budget_endpoints.router)

# Import AI categorization function
from ai_categorization import categorize_with_ai, fallback_categorization

# Auto-categorize expenses - will try AI first, then fallback to keywords
async def auto_categorize(description: str, amount: float = 0) -> str:
    try:
        # First try AI categorization
        category = await categorize_with_ai(description, amount)
        return category
    except Exception as e:
        # If AI categorization fails, use fallback
        print(f"AI categorization failed: {str(e)}")
        return fallback_categorization(description)

# Get all expenses
@app.get("/expenses/", response_model=List[ExpenseInDB])
async def get_expenses(db: Session = Depends(get_db)):
    expenses = db.query(ExpenseModel).all()
    return expenses

# Add a new expense
@app.post("/add_expense/", response_model=ExpenseInDB)
async def add_expense(expense: Expense, db: Session = Depends(get_db)):
    # Auto-categorize if no category provided
    if not expense.category:
        expense.category = await auto_categorize(expense.description, expense.amount)
    
    # Create a new expense with ID
    db_expense = ExpenseModel(**expense.dict())
    
    # Add to database
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    return db_expense

# Get expense by ID
@app.get("/expenses/{expense_id}", response_model=ExpenseInDB)
async def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(ExpenseModel).filter(ExpenseModel.id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

# Delete expense
@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(ExpenseModel).filter(ExpenseModel.id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}

# Get expenses by category
@app.get("/expenses/category/{category}", response_model=List[ExpenseInDB])
async def get_expenses_by_category(category: str, db: Session = Depends(get_db)):
    filtered_expenses = db.query(ExpenseModel).filter(ExpenseModel.category.ilike(f"%{category}%")).all()
    return filtered_expenses

# Get total amount spent
@app.get("/total/")
async def get_total(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(func.sum(ExpenseModel.amount)).scalar() or 0
    return {"total": total}

# Import expenses from CSV
@app.post("/import_expenses/", response_model=List[ExpenseInDB])
async def import_expenses(expenses: List[Expense], db: Session = Depends(get_db)):
    imported_expenses = []
    for expense in expenses:
        # Auto-categorize if no category provided
        if not expense.category:
            expense.category = await auto_categorize(expense.description, expense.amount)
        
        # Create a new expense with ID
        db_expense = ExpenseModel(**expense.dict())
        
        # Add to database
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        
        imported_expenses.append(db_expense)
    
    return imported_expenses

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)