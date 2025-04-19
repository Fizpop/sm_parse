from fastapi import APIRouter, UploadFile, HTTPException
from typing import List, Dict
import logging
from ..services.search_service import search_service
from ..services.file_service import file_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/v1/search-media")
async def search_media(query: str) -> List[Dict]:
    """
    Search for media sources using the provided query.
    Returns a list of media sources with metadata.
    """
    try:
        results = search_service.search_media(query)
        return results
    except Exception as e:
        logger.error(f"Error in search_media endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/upload-csv")
async def upload_csv(file: UploadFile) -> List[Dict]:
    """
    Upload and process a CSV file containing media sources.
    Returns a list of processed media sources.
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
            
        # Save and process the file
        file_path = file_service.save_file(file)
        results = file_service.process_csv(file_path)
        
        return results
    except Exception as e:
        logger.error(f"Error in upload_csv endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 