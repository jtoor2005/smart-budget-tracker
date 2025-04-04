import httpx
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file (create this file in your backend directory)
load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Function to categorize expenses using OpenAI API
async def categorize_with_ai(description: str, amount: float) -> str:
    """
    Use OpenAI API to categorize an expense based on its description and amount.
    Returns a category from a predefined list.
    """
    # Define available categories
    categories = [
        "Food", "Shopping", "Transportation", "Entertainment", 
        "Utilities", "Housing", "Healthcare", "Other", "Furniture"
    ]
    
    # If no API key is set, use fallback method
    if not OPENAI_API_KEY:
        print("Warning: No OpenAI API key found. Using fallback categorization.")
        return fallback_categorization(description)
    
    # Create prompt for OpenAI
    prompt = f"""
    Categorize this expense into exactly one of these categories: {', '.join(categories)}
    
    Expense description: {description}
    Amount: ${amount}
    
    Respond with only the category name, nothing else.
    """
    
    # Make request to OpenAI API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are an AI assistant that categorizes expenses accurately."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Lower temperature for more predictable outputs
                    "max_tokens": 10
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                response_data = response.json()
                category = response_data["choices"][0]["message"]["content"].strip()
                
                # Ensure the category is valid
                if category in categories:
                    return category
                else:
                    # Default to "Other" if the AI didn't return a valid category
                    return "Other"
            else:
                # If API call fails, use fallback method
                print(f"OpenAI API request failed with status code {response.status_code}")
                return fallback_categorization(description)
                
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return fallback_categorization(description)

# Fallback categorization method if API call fails
def fallback_categorization(description: str) -> str:
    """Simple keyword-based categorization as a fallback"""
    description = description.lower()
    
    if any(word in description for word in ["restaurant", "food", "grocery", "coffee", "meal"]):
        return "Food"
    elif any(word in description for word in ["movie", "game", "concert", "netflix", "spotify"]):
        return "Entertainment"
    elif any(word in description for word in ["uber", "lyft", "gas", "train", "bus", "taxi"]):
        return "Transportation"
    elif any(word in description for word in ["rent", "mortgage", "repair"]):
        return "Housing"
    elif any(word in description for word in ["electric", "water", "internet", "phone"]):
        return "Utilities"
    elif any(word in description for word in ["doctor", "medicine", "pharmacy", "hospital"]):
        return "Healthcare"
    elif any(word in description for word in ["amazon", "walmart", "target", "clothes", "shoes"]):
        return "Shopping"
    elif any(word in description for word in ["table", "chair", "sofa", "desk", "bed"]):
        return "Furniture"
    else:
        return "Other"