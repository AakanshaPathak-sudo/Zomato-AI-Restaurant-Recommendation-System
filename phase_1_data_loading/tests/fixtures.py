"""Minimal in-memory rows matching Hugging Face raw schema (for fast tests)."""

import pandas as pd

from phase_1_data_loading.schema import RAW_COLUMNS


def minimal_zomato_dataframe(n_rows: int = 2) -> pd.DataFrame:
    """Build a small DataFrame with every RAW_COLUMNS present."""
    rows = []
    for i in range(n_rows):
        row = {
            "url": f"https://zomato.com/r{i}",
            "address": f"{i} Main St",
            "name": f"Restaurant {i}",
            "online_order": "Yes",
            "book_table": "No",
            "rate": "4.1/5" if i == 0 else "3.5/5",
            "votes": 100 + i,
            "phone": "08012345678",
            "location": "Area A",
            "rest_type": "Casual Dining",
            "dish_liked": "Biryani",
            "cuisines": "North Indian, Chinese",
            "approx_cost(for two people)": "800" if i == 0 else "1,200",
            "reviews_list": "[]",
            "menu_item": "[]",
            "listed_in(type)": "Delivery",
            "listed_in(city)": "Bangalore" if i == 0 else " Mumbai ",
        }
        rows.append([row[c] for c in RAW_COLUMNS])
    df = pd.DataFrame(rows, columns=list(RAW_COLUMNS))
    return df
