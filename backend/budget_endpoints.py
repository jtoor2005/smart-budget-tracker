from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models import BudgetModel

router = APIRouter()

# Pydantic model for budget
class Budget(BaseModel):
    category: str
    amount: float
    period: str = "monthly"

class BudgetInDB(Budget):
    id: int

# Get all budgets
@router.get("/budgets/", response_model=List[BudgetInDB])
async def get_budgets(db: Session = Depends(get_db)):
    budgets = db.query(BudgetModel).all()
    return budgets

# Add a new budget
@router.post("/budgets/", response_model=BudgetInDB)
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
@router.get("/budgets/{budget_id}", response_model=BudgetInDB)
async def get_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(BudgetModel).filter(BudgetModel.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

# Delete budget
@router.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(BudgetModel).filter(BudgetModel.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}

# Get budget status - compare with actual expenses
@router.get("/budget_status/")
async def get_budget_status(db: Session = Depends(get_db)):
    from models import ExpenseModel
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