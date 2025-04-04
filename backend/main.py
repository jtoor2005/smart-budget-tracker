from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import random

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

# Sample categories for auto-categorization (simple version)
categories = [
    "Food", "Shopping", "Transportation", "Entertainment", 
    "Utilities", "Housing", "Healthcare", "Other"
]

# In-memory database (replace with actual database in production)
expenses_db = []

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
async def get_expenses():
    return expenses_db

# Add a new expense
@app.post("/add_expense/", response_model=ExpenseInDB)
async def add_expense(expense: Expense):
    # Auto-categorize if no category provided
    if not expense.category:
        expense.category = await auto_categorize(expense.description, expense.amount)
    
    # Create a new expense with ID
    new_id = len(expenses_db) + 1
    expense_db = ExpenseInDB(id=new_id, **expense.dict())
    
    # Add to database
    expenses_db.insert(0, expense_db)  # Insert at the beginning to match frontend behavior
    
    return expense_db

# Get expense by ID
@app.get("/expenses/{expense_id}", response_model=ExpenseInDB)
async def get_expense(expense_id: int):
    for expense in expenses_db:
        if expense.id == expense_id:
            return expense
    raise HTTPException(status_code=404, detail="Expense not found")

# Delete expense
@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int):
    for i, expense in enumerate(expenses_db):
        if expense.id == expense_id:
            expenses_db.pop(i)
            return {"message": "Expense deleted successfully"}
    raise HTTPException(status_code=404, detail="Expense not found")

# Get expenses by category
@app.get("/expenses/category/{category}", response_model=List[ExpenseInDB])
async def get_expenses_by_category(category: str):
    filtered_expenses = [expense for expense in expenses_db if expense.category.lower() == category.lower()]
    return filtered_expenses

# Get total amount spent
@app.get("/total/")
async def get_total():
    total = sum(expense.amount for expense in expenses_db)
    return {"total": total}

# Import expenses from CSV
@app.post("/import_expenses/", response_model=List[ExpenseInDB])
async def import_expenses(expenses: List[Expense]):
    imported_expenses = []
    for expense in expenses:
        # Auto-categorize if no category provided
        if not expense.category:
            expense.category = auto_categorize(expense.description)
        
        # Create a new expense with ID
        new_id = len(expenses_db) + 1
        expense_db = ExpenseInDB(id=new_id, **expense.dict())
        
        # Add to database
        expenses_db.append(expense_db)
        imported_expenses.append(expense_db)
    
    return imported_expenses

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)