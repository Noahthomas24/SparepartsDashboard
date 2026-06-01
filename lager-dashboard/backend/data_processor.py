import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()


def generate_inventory_insight(
    analyse_data: list[dict], user_question: str = ""
) -> dict:

    # os.getenv trækker api key ud
    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "MISTRAL_API_KEY mangler i miljøvariablerne.",
        }

    return {"status": "success", "data": "Insights fra mistral"}


def process_inventory_data(df: pd.DataFrame) -> dict:

    # Forventer en DataFrame med kolonnerne: 'date', 'product_id', 'demand'

    # Standardiserer kolonnenavne for at undgå errors
    df.columns = df.columns.str.lower().str.strip()

    # Tjek om de påkrævede kolonner findes
    required_columns = {"date", "product_id", "demand"}
    if not required_columns.issubset(df.columns):
        return {
            "status": "error",
            "message": f"Mangler kolonner. Forventede mindst: {required_columns}, men fik: {list(df.columns)}",
        }

    # Konverter "date" til rigtige datetime-objekter
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Fjern eventuelle rækker, hvor datoen ikke kunne læses
    df = df.dropna(subset=["date"])

    # Sikrer at current_stock er tal
    df["demand"] = pd.to_numeric(df["demand"], errors="coerce").fillna(0)

    # Grouping
    forbrug = df.groupby("product_id")["demand"].sum().reset_index()
    forbrug = forbrug.rename(columns={"demand": "total_usage"})

    # Find første dato, sidste dato og antal gange produktet er bestilt
    tidslinje = (
        df.groupby("product_id")
        .agg(
            first_date=("date", "min"),
            last_date=("date", "max"),
            antal_ordrer=("date", "count"),
        )
        .reset_index()
    )

    # merge på produktets navn/ID
    analyse_df = pd.merge(forbrug, tidslinje, on="product_id")

    daily_demand = df.groupby(["product_id", "date"])["demand"].sum().reset_index()
    avg_daily_demand = daily_demand.groupby("product_id")["demand"].mean().reset_index()
    avg_daily_demand.rename(
        columns={"demand": "gennemsnitlig_daglig_brug"}, inplace=True
    )
    avg_daily_demand["gennemsnitlig_daglig_brug"] = avg_daily_demand[
        "gennemsnitlig_daglig_brug"
    ].round(2)

    analyse_df = pd.merge(analyse_df, avg_daily_demand, on="product_id")

    analyse_df["time_span"] = (
        analyse_df["last_date"] - analyse_df["first_date"]
    ).dt.days

    analyse_df["forbrug_per_dag"] = np.where(
        analyse_df["time_span"] > 0,
        np.round(analyse_df["total_usage"] / analyse_df["time_span"], 2),
        analyse_df["total_usage"].astype(float),
    )

    # Konverter datetimes til strings, så FastAPI kan sende det som JSON
    analyse_df["first_date"] = analyse_df["first_date"].dt.strftime("%Y-%m-%d")
    analyse_df["last_date"] = analyse_df["last_date"].dt.strftime("%Y-%m-%d")

    # Returner data struktureret
    return {"status": "success", "data": analyse_df.to_dict(orient="records")}
