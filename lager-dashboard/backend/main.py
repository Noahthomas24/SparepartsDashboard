from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

# Importerer da_processor.py
from data_processor import process_inventory_data

# Importerer LLM service
from llm_service import generate_inventory_insight

app = FastAPI(
    title="Lager Dashboard API",
    description="API til håndtering af lagerdata og AI-analyse",
    version="1.0.0",
)

# Tillad kommunikation fra Streamlit (Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.endswith(
        ".csv"
    ):  # if not file.filename or not file.filename.endswith(".csv")
        raise HTTPException(status_code=400, detail="Filen skal være en csv fil")
    try:
        contents = await file.read()

        # Konverter bytes til et format som Pandas kan læse.
        csv_data = io.BytesIO(contents)

        # Indlæst i dataframe
        df = pd.read_csv(csv_data)

        # Summary som kan sendes til frontend
        summary = {
            "filnavn": file.filename,
            "antal_rækker": len(df),
            "kolonner": df.columns.tolist(),
        }

        processed_result = process_inventory_data(df)

        if processed_result["status"] == "error":
            raise HTTPException(status_code=400, detail=processed_result["message"])

        analyse_data = processed_result["data"]
        ai_response = generate_inventory_insight(analyse_data, user_question="")

        return {
            "status": "data modtaget",
            "data_summary": summary,
            "analyse_resultat": processed_result["data"],
            "ai_response": ai_response,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"der opstod en fejl ved indlæsning af filen: {str(e)}",
        )
