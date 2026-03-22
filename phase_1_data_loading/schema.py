"""Column names and constants for ManikaSaini/zomato-restaurant-recommendation."""

# Raw column names as published on Hugging Face (train split).
RAW_COLUMNS = (
    "url",
    "address",
    "name",
    "online_order",
    "book_table",
    "rate",
    "votes",
    "phone",
    "location",
    "rest_type",
    "dish_liked",
    "cuisines",
    "approx_cost(for two people)",
    "reviews_list",
    "menu_item",
    "listed_in(type)",
    "listed_in(city)",
)

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
DEFAULT_SPLIT = "train"

# Canonical names after cleaning (downstream phases use these).
COL_CITY = "city"
COL_APPROX_COST_FOR_TWO = "approx_cost_for_two"
COL_RATE_NUMERIC = "rate_numeric"
