from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import random
from sqlalchemy.orm import Session

# Import database and models
from database import get_db, engine
from models import Base, ExpenseModel, BudgetModel

# Create all tables in the database
Base.metadata.create_all(bind=engine)

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

# Budget model
class Budget(BaseModel):
    category: str
    amount: float
    period: str = "monthly"

class BudgetInDB(Budget):
    id: int

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

# Get all budgets
@app.get("/budgets/", response_model=List[BudgetInDB])
async def get_budgets(db: Session = Depends(get_db)):
    budgets = db.query(BudgetModel).all()
    return budgets

# Add a new budget
@app.post("/budgets/", response_model=BudgetInDB)
async def add_budget(budget: Budget, db: Session = Depends(get_db)):
    # Check if budget for this category already exists
    existing_budget = db.query(BudgetModel).filter(BudgetModel.category == budget.category).first()
    
    if existing_budget:
        # Update existing budget
        existing_budget.amount = budget.amount
        existing_budget.period = budget.period
        db.commit()
        db.refresh(existing_budget)
        return existing_budget
    
    # Create new budget
    db_budget = BudgetModel(**budget.dict())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

# Get budget by ID
@app.get("/budgets/{budget_id}", response_model=BudgetInDB)
async def get_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(BudgetModel).filter(BudgetModel.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

# Delete budget
@app.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(BudgetModel).filter(BudgetModel.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}

# Get budget status - compare with actual expenses
@app.get("/budget_status/")
async def get_budget_status(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # Get all budgets
    budgets = db.query(BudgetModel).all()
    
    # Calculate the total expenses for each category
    category_expenses = db.query(
        ExpenseModel.category,
        func.sum(ExpenseModel.amount).label("total")
    ).group_by(ExpenseModel.category).all()
    
    # Convert to dictionary for easy lookup
    expenses_dict = {item.category: item.total for item in category_expenses}
    
    # Create budget status report
    budget_status = []
    for budget in budgets:
        spent = expenses_dict.get(budget.category, 0)
        remaining = budget.amount - spent
        percentage = (spent / budget.amount) * 100 if budget.amount > 0 else 0
        
        budget_status.append({
            "category": budget.category,
            "budget_amount": budget.amount,
            "spent": spent,
            "remaining": remaining,
            "percentage_used": percentage,
            "status": "over_budget" if percentage > 100 else "on_track"
        })
    
    return budget_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)