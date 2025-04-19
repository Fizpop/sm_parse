import os
import logging
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import pandas as pd
from bson import ObjectId

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        # Підключення до MongoDB
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client.media_sources
        
        # Колекції
        self.known_sources = self.db.known_sources  # Джерела з CSV
        self.new_sources = self.db.new_sources      # Нові знайдені джерела
        
    async def init_db(self):
        """Ініціалізація бази даних та індексів."""
        try:
            # Створюємо унікальні індекси по URL
            await self.known_sources.create_index("url", unique=True)
            await self.new_sources.create_index("url", unique=True)
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")
            
    async def import_from_csv(self, csv_path: str):
        """Імпорт джерел з CSV файлу."""
        try:
            # Читаємо CSV файл
            df = pd.read_csv(csv_path)
            
            # Перетворюємо дані в потрібний формат
            sources = []
            for _, row in df.iterrows():
                source = {
                    "name": row.get("Назва", ""),
                    "url": row.get("Адреса", ""),
                    "social_alias": row.get("Соціальний псевдонім", ""),
                    "media_type": row.get("Медіа Тип", ""),
                    "super_type": row.get("Super Type", ""),
                    "region": row.get("Регіон", ""),
                    "imported_at": datetime.utcnow(),
                    "source": "csv_import"
                }
                sources.append(source)
            
            # Вставляємо дані в колекцію known_sources
            if sources:
                await self.known_sources.insert_many(sources, ordered=False)
            logger.info(f"Imported {len(sources)} sources from CSV")
            
        except Exception as e:
            logger.error(f"Error importing from CSV: {str(e)}")
            
    async def add_new_source(self, source: Dict):
        """Додавання нового джерела."""
        try:
            # Перевіряємо чи джерело вже існує
            existing = await self.known_sources.find_one({"url": source["url"]})
            if existing:
                logger.info(f"Source {source['url']} already exists in known_sources")
                return
                
            existing = await self.new_sources.find_one({"url": source["url"]})
            if existing:
                logger.info(f"Source {source['url']} already exists in new_sources")
                return
                
            # Додаємо timestamp
            source["found_at"] = datetime.utcnow()
            
            # Вставляємо нове джерело
            await self.new_sources.insert_one(source)
            logger.info(f"Added new source: {source['url']}")
            
        except Exception as e:
            logger.error(f"Error adding new source: {str(e)}")
            
    async def get_known_sources(self) -> List[Dict]:
        """Отримання списку відомих джерел."""
        try:
            cursor = self.known_sources.find({})
            sources = await cursor.to_list(length=None)
            return sources
        except Exception as e:
            logger.error(f"Error getting known sources: {str(e)}")
            return []
            
    async def get_new_sources(self) -> List[Dict]:
        """Отримання списку нових джерел."""
        try:
            cursor = self.new_sources.find({})
            sources = await cursor.to_list(length=None)
            return sources
        except Exception as e:
            logger.error(f"Error getting new sources: {str(e)}")
            return []
            
    async def export_new_sources_to_csv(self, output_path: str):
        """Експорт нових джерел у CSV."""
        try:
            # Отримуємо всі нові джерела
            sources = await self.get_new_sources()
            
            # Створюємо DataFrame
            df = pd.DataFrame(sources)
            
            # Зберігаємо у CSV
            df.to_csv(output_path, index=False)
            logger.info(f"Exported {len(sources)} new sources to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            
    async def sync_sources(self):
        """Синхронізація джерел між колекціями."""
        try:
            # Отримуємо всі нові джерела
            new_sources = await self.get_new_sources()
            
            # Переміщуємо підтверджені джерела
            for source in new_sources:
                if source.get("is_verified", False):
                    # Видаляємо з нових джерел
                    await self.new_sources.delete_one({"_id": source["_id"]})
                    
                    # Додаємо до відомих джерел
                    source["moved_at"] = datetime.utcnow()
                    await self.known_sources.insert_one(source)
                    
            logger.info("Sources synchronized successfully")
            
        except Exception as e:
            logger.error(f"Error synchronizing sources: {str(e)}")

db_service = DBService() 