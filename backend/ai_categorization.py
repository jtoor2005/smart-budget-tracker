import httpx
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file (create this file in your backend directory)
load_dotenv()

# Get Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Function to categorize expenses using Gemini API
async def categorize_with_ai(description: str, amount: float) -> str:
    """
    Use Google's Gemini API to categorize an expense based on its description and amount.
    Returns a category from a predefined list.
    """
    # Define available categories
    categories = [
        "Food", "Shopping", "Transportation", "Entertainment", 
        "Utilities", "Housing", "Healthcare", "Other", "Furniture"
    ]
    
    # If no API key is set, use fallback method
    if not GEMINI_API_KEY:
        print("Warning: No Gemini API key found. Using fallback categorization.")
        return fallback_categorization(description)
    
    # Create prompt for Gemini
    prompt = f"""
    Categorize this expense into exactly one of these categories: {', '.join(categories)}
    
    Expense description: {description}
    Amount: ${amount}
    
    Respond with only the category name, nothing else.
    """
    
    # Make request to Gemini API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers={
                    "Content-Type": "application/json"
                },
                params={
                    "key": GEMINI_API_KEY
                },
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 10
                    }
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Extract the text from the Gemini response
                text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Find which category is in the response
                for category in categories:
                    if category.lower() in text.lower():
                        return category
                
                # If no exact match, try to find the closest match
                return find_closest_category(text, categories)
            else:
                # If API call fails, use fallback method
                print(f"Gemini API request failed with status code {response.status_code}")
                print(f"Response: {response.text}")
                return fallback_categorization(description)
                
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return fallback_categorization(description)

def find_closest_category(text, categories):
    """Find the most likely category from the API response"""
    text_lower = text.lower()
    
    # First try exact matches
    for category in categories:
        if category.lower() in text_lower:
            return category
    
    # If no match, return "Other"
    return "Other"

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