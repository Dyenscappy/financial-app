from fastapi import FastAPI, HTTPException
import requests
from database import get_db_connection

app = FastAPI()

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
