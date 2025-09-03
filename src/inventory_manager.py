from datetime import datetime
import pandas as pd

def predict_demand(db, title, days=7):
    """Predict book demand based on recent sales history."""
    revenue_df = db.get_revenue()
    book_id = db.get_book_id(title)
    recent_sales = revenue_df[revenue_df['book_id'] == book_id]['quantity'].tail(days).mean()

    if pd.isna(recent_sales):
        return 0

    current_month = datetime.now().month
    # Example: August considered high season
    season_factor = 1.5 if current_month == 8 else 1.0

    suggested_quantity = int(recent_sales * season_factor * 1.2)  # 20% buffer + seasonal factor
    message = f"Predicted demand for '{title}': {suggested_quantity} copies (Season factor: {season_factor}x)."
    return message


def analyze_profit(db):
    """Analyze profit, revenue, and expenses."""
    revenue_df = db.get_revenue()
    expenses_df = db.get_expenses()

    total_revenue = revenue_df['total_amount'].sum()
    total_expenses = expenses_df['total_cost'].sum()
    profit = total_revenue - total_expenses

    if profit < 0:
        message = f"Negative profit: {profit} VND. Consider reducing costs or adjusting prices."
    else:
        message = f"Profit: {profit} VND | Revenue: {total_revenue} VND | Expenses: {total_expenses} VND."

    # Simple recommendation
    if profit < 1_000_000:
        message += "\nSuggestion: Increase prices for certain categories to optimize profit."
    else:
        message += "\nSuggestion: Offer book combos or promotions to boost revenue."
    return message


def check_inventory(db, title):
    """Check and suggest restocking for a book."""
    quantity = predict_demand(db, title)
    if isinstance(quantity, str):
        return quantity
    if quantity > 0:
        return f"Suggested restock: {quantity} copies of '{title}'."
    return f"No additional stock needed for '{title}'."