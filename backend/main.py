from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

# Load API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("❌ Gemini API key is missing! Set GEMINI_API_KEY environment variable.")

# Configure Google Gemini API
genai.configure(api_key=api_key)

app = FastAPI()

class Expense(BaseModel):
    description: str
    amount: float

@app.post("/add_expense/")
def add_expense(expense: Expense):
    """Adds an expense and categorizes it using Gemini AI API."""
    try:
        category = categorize_expense(expense.description)
        return {"description": expense.description, "amount": expense.amount, "category": category}
    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"AI categorization failed: {str(e)}")

def categorize_expense(description):
    """Uses Google Gemini API to categorize an expense."""
    try:
        print(f"🔹 Sending request to Gemini AI for: {description}")  # Debug log

        model_name = "models/gemini-1.5-pro-latest"  # Change this to another model if needed

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            f"Categorize this expense into Food, Rent, Shopping, Bills, Furniture, etc.: {description}"
        )

        # Debugging logs
        print("🔹 Full Gemini AI Response:", response)  # Print full response
        
        if response and hasattr(response, 'text'):
            category = response.text.strip()
            print(f"✅ Categorized as: {category}")
            return category
        else:
            print("❌ Gemini AI returned an empty response")
            return "Unknown"
    
    except Exception as e:
        print(f"❌ Google Gemini API Error: {e}")  # Logs error
        return "Unknown"

@app.get("/")
def root():
    return {"message": "Welcome to Smart Budget Tracker API"}

@app.get("/expenses/")
def list_expenses():
    """Returns all expenses (dummy data for now)."""
    return [
        {"description": "Groceries", "amount": 50, "category": "Food"},
        {"description": "Netflix Subscription", "amount": 15, "category": "Entertainment"}
    ]
