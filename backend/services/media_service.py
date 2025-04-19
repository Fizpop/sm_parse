from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from .mongo_service import MongoService

logger = logging.getLogger(__name__)

class MediaService:
    def __init__(self, mongo_service: MongoService):
        self.mongo = mongo_service
        self.collection = "media_sources"

    async def setup(self):
        """Setup indexes and initial configuration."""
        await self.mongo.create_index(
            self.collection, 
            [("url", 1)],  # 1 for ascending index
            unique=True
        )

    async def add_media_source(self, source_data: Dict[str, Any]) -> str:
        """Add a new media source to the database."""
        source_data["created_at"] = datetime.utcnow()
        source_data["updated_at"] = datetime.utcnow()
        
        try:
            return await self.mongo.insert_one(self.collection, source_data)
        except Exception as e:
            logger.error(f"Error adding media source: {e}")
            raise

    async def add_many_media_sources(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Add multiple media sources to the database."""
        current_time = datetime.utcnow()
        for source in sources:
            source["created_at"] = current_time
            source["updated_at"] = current_time
        
        try:
            return await self.mongo.insert_many(self.collection, sources)
        except Exception as e:
            logger.error(f"Error adding media sources: {e}")
            raise

    async def get_media_source(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a single media source by query."""
        try:
            return await self.mongo.find_one(self.collection, query)
        except Exception as e:
            logger.error(f"Error getting media source: {e}")
            raise

    async def get_media_sources(self, query: Dict[str, Any] = None, 
                              skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get multiple media sources with pagination."""
        query = query or {}
        try:
            return await self.mongo.find_many(self.collection, query, skip, limit)
        except Exception as e:
            logger.error(f"Error getting media sources: {e}")
            raise

    async def update_media_source(self, query: Dict[str, Any], 
                                update_data: Dict[str, Any]) -> bool:
        """Update a media source."""
        update_data["updated_at"] = datetime.utcnow()
        try:
            return await self.mongo.update_one(self.collection, query, update_data)
        except Exception as e:
            logger.error(f"Error updating media source: {e}")
            raise

    async def delete_media_source(self, query: Dict[str, Any]) -> bool:
        """Delete a media source."""
        try:
            return await self.mongo.delete_one(self.collection, query)
        except Exception as e:
            logger.error(f"Error deleting media source: {e}")
            raise

    async def count_media_sources(self, query: Dict[str, Any] = None) -> int:
        """Count media sources matching the query."""
        query = query or {}
        try:
            return await self.mongo.count_documents(self.collection, query)
        except Exception as e:
            logger.error(f"Error counting media sources: {e}")
            raise

    async def get_media_sources_by_type(self, media_type: str, 
                                      skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get media sources by type."""
        query = {"media_type": media_type}
        return await self.get_media_sources(query, skip, limit)

    async def get_media_sources_by_region(self, region: str, 
                                        skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get media sources by region."""
        query = {"region": region}
        return await self.get_media_sources(query, skip, limit)

    async def search_media_sources(self, search_text: str, 
                                 skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search media sources by text in name or description."""
        query = {
            "$or": [
                {"name": {"$regex": search_text, "$options": "i"}},
                {"description": {"$regex": search_text, "$options": "i"}}
            ]
        }
        return await self.get_media_sources(query, skip, limit) 