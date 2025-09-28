from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from app.services import preprocessing
import uuid
import pandas as pd

router = APIRouter()

# In-memory dataset store (simple, replace with Redis if needed)
DATASETS = {}


@router.post("/")
async def upload_files(
    files: List[UploadFile] = File(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
):
    """
    Accept multiple JSON files + timeframe
    Returns a dataset_id for fetching metrics
    """
    try:
        file_bytes_list = [await f.read() for f in files]
        df = preprocessing.merge_and_preprocess(file_bytes_list)
        

        
        # Set timestamp as index for fast filtering & timezone awareness if needed
        df.set_index("ts", inplace=True)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        
    except Exception as e:
        return {"error": str(e)}

    # Generate dataset_id
    dataset_id = str(uuid.uuid4())
    # Store in memory (for demo)
    DATASETS[dataset_id] = df

    # Filter by timeframe for preview
    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)
    preview_df = df.loc[start_dt:end_dt]

    # Return basic info + small sample for frontend
    sample = preview_df.head(5).to_dict(orient="records")
    return {
        "dataset_id": dataset_id,
        "row_count": len(preview_df),
        "sample": sample
    }
