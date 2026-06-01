import pandas as pd

from data_processor import process_inventory_data


def test_missing_columns():
    df = pd.DataFrame({"date": ["2023-01-01"], "demand": [10]})

    result = process_inventory_data(df)
    assert result["status"] == "error"
    assert "Mangler kolonner" in result["message"]


def test_successful_processing():
    data = {
        "Date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "product_id": ["Product 1", "Product 2", "Product 3"],
        "demand": [10, 20, 30],
    }

    df = pd.DataFrame(data)
    result = process_inventory_data(df)

    assert result["status"] == "success"
    assert result["data"][0]["product_id"] == "Product 1"
