from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from backend.database import get_db_connection

app = FastAPI()

# ✅ Add CORS Middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later to only your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENCY_API_URL = "https://api.frankfurter.app/latest"

# ✅ Currency Converter Endpoint
@app.get("/convert")
def convert_currency(amount: float, from_currency: str, to_currency: str):
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    response = requests.get(f"{CURRENCY_API_URL}?from={from_currency}&to={to_currency}")
    data = response.json()

    if "rates" not in data or to_currency not in data["rates"]:
        raise HTTPException(status_code=400, detail="Invalid currency")

    converted_amount = amount * data["rates"][to_currency]

    return {
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "converted_amount": round(converted_amount, 2)  # ✅ Round to 2 decimal places
    }


# ✅ Expense Tracker Endpoints
@app.post("/expenses")
def add_expense(description: str, amount: float, currency: str, target_currency: str = "USD"):
    response = requests.get(f"{CURRENCY_API_URL}?from={currency}&to={target_currency}")
    data = response.json()

    if "rates" not in data or target_currency not in data["rates"]:
        raise HTTPException(status_code=400, detail="Invalid currency")

    converted_amount = amount * data["rates"][target_currency]

    # ✅ Round the converted amount to 2 decimal places before saving
    converted_amount = round(converted_amount, 2)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (description, amount, currency, converted_amount) VALUES (?, ?, ?, ?)",
                   (description, amount, currency, converted_amount))
    conn.commit()
    conn.close()

    return {"message": "Expense added successfully", "converted_amount": converted_amount}

@app.get("/expenses")
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, currency, converted_amount FROM expenses")
    expenses = cursor.fetchall()
    conn.close()

    # Convert database rows to dictionary format
    expense_list = [
        {
            "id": row[0],
            "description": row[1],
            "amount": row[2],
            "currency": row[3],
            "converted_amount": row[4]
        }
        for row in expenses
    ]

    return {"expenses": expense_list}


# ✅ DELETE Endpoint to Remove an Expense by ID
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the expense exists
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    expense = cursor.fetchone()

    if expense is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found")

    # Delete the expense
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

    return {"message": "Expense deleted successfully"}
