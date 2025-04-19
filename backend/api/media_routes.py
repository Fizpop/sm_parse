from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import pandas as pd
from ..models.database import get_db, KnownSource, NewSource
from ..services.search_service import search_service
from ..services.db_service import db_service
from pydantic import BaseModel
from datetime import datetime
import logging
import os

router = APIRouter()

class SearchQuery(BaseModel):
    query: str

class MediaResponse(BaseModel):
    title: str
    url: str
    domain: str
    description: str
    rss_feed: Optional[str] = None
    last_updated: Optional[str] = None
    found_at: str

class SourceResponse(BaseModel):
    domain: str
    name: str
    url: str
    created_at: Optional[str] = None
    found_at: Optional[str] = None

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        
        # Зберігаємо дані в БД
        for _, row in df.iterrows():
            domain = row.get('domain', '').strip()
            name = row.get('name', '').strip()
            url = row.get('url', '').strip()
            
            # Пропускаємо рядки з порожнім доменом
            if not domain:
                continue
                
            # Перевіряємо чи існує вже таке джерело
            existing_source = db.query(KnownSource).filter(KnownSource.domain == domain).first()
            
            if existing_source:
                # Оновлюємо існуюче джерело
                existing_source.name = name
                existing_source.url = url
            else:
                # Створюємо нове джерело
                source = KnownSource(
                    domain=domain,
                    name=name,
                    url=url
                )
                db.add(source)
        
        db.commit()
        return {"message": "CSV file processed successfully"}
    
    except Exception as e:
        db.rollback()  # Відкатуємо зміни у випадку помилки
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-media")
async def search_media(query: str) -> List[Dict]:
    """Пошук нових медіа джерел."""
    try:
        # Виконуємо пошук
        results = search_service.search_media(query)
        
        # Зберігаємо результати в базу даних
        for result in results:
            await db_service.add_new_source(result)
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/known-sources")
async def get_known_sources() -> List[Dict]:
    """Отримання списку відомих джерел."""
    try:
        return await db_service.get_known_sources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new-sources")
async def get_new_sources() -> List[Dict]:
    """Отримання списку нових джерел."""
    try:
        return await db_service.get_new_sources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-csv")
async def import_csv(csv_path: str):
    """Імпорт джерел з CSV файлу."""
    try:
        await db_service.import_from_csv(csv_path)
        return {"message": "CSV imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-new-sources")
async def export_new_sources():
    """Експорт нових джерел у CSV."""
    try:
        # Створюємо ім'я файлу з поточною датою
        filename = f"new_sources_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        output_path = os.path.join(os.getcwd(), filename)
        
        await db_service.export_new_sources_to_csv(output_path)
        return {"message": "Sources exported successfully", "file_path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-sources")
async def sync_sources():
    """Синхронізація джерел між колекціями."""
    try:
        await db_service.sync_sources()
        return {"message": "Sources synchronized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-source/{source_id}")
async def verify_source(source_id: str):
    """Підтвердження нового джерела."""
    try:
        # Оновлюємо статус джерела
        await db_service.new_sources.update_one(
            {"_id": source_id},
            {"$set": {"is_verified": True, "verified_at": datetime.utcnow()}}
        )
        return {"message": "Source verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 