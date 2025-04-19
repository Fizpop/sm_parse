from typing import List, Dict, Any, Optional, Union, AsyncIterator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self, connection_string: str, database_name: str):
        """Initialize MongoDB service with connection string and database name.
        
        Args:
            connection_string (str): MongoDB connection URI
            database_name (str): Name of the database to use
        """
        self._connection_string = connection_string
        self._database_name = database_name
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self._client = AsyncIOMotorClient(self._connection_string)
            self._db = self._client[self._database_name]
            # Test connection
            await self._client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {self._database_name}")
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    def _convert_id(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ObjectId to string in document."""
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    def _to_object_id(self, id_str: str) -> ObjectId:
        """Convert string ID to ObjectId."""
        try:
            return ObjectId(id_str)
        except InvalidId as e:
            logger.error(f"Invalid ObjectId format: {id_str}")
            raise ValueError(f"Invalid ID format: {id_str}") from e

    async def create_index(self, collection: str, keys: List[tuple], unique: bool = False) -> str:
        """Create an index on the specified collection.
        
        Args:
            collection (str): Collection name
            keys (List[tuple]): List of (key, direction) pairs
            unique (bool): Whether the index should be unique
        
        Returns:
            str: Name of the created index
        """
        try:
            result = await self._db[collection].create_index(keys, unique=unique)
            logger.info(f"Created index '{result}' on collection {collection}")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to create index on {collection}: {str(e)}")
            raise

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document into collection.
        
        Args:
            collection (str): Collection name
            document (Dict): Document to insert
            
        Returns:
            str: ID of inserted document
        """
        try:
            result = await self._db[collection].insert_one(document)
            inserted_id = str(result.inserted_id)
            logger.info(f"Successfully inserted document with ID: {inserted_id}")
            return inserted_id
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error while inserting document: {str(e)}")
            raise
        except PyMongoError as e:
            logger.error(f"Failed to insert document: {str(e)}")
            raise

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query.
        
        Args:
            collection (str): Collection name
            query (Dict): Query filter
            
        Returns:
            Optional[Dict]: Found document or None
        """
        try:
            result = await self._db[collection].find_one(query)
            if result:
                logger.debug(f"Found document in {collection}")
                return self._convert_id(result)
            logger.debug(f"No document found in {collection} matching query")
            return None
        except PyMongoError as e:
            logger.error(f"Error finding document in {collection}: {str(e)}")
            raise

    async def find_many(self, collection: str, query: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Find multiple documents matching the query.
        
        Args:
            collection (str): Collection name
            query (Dict): Query filter
            
        Yields:
            Dict: Found documents
        """
        try:
            cursor = self._db[collection].find(query)
            async for doc in cursor:
                yield self._convert_id(doc)
            logger.debug(f"Completed fetching documents from {collection}")
        except PyMongoError as e:
            logger.error(f"Error finding documents in {collection}: {str(e)}")
            raise

    async def update_one(self, collection: str, query: Dict[str, Any], 
                        update: Dict[str, Any]) -> bool:
        """Update a single document matching the query.
        
        Args:
            collection (str): Collection name
            query (Dict): Query filter
            update (Dict): Update operations
            
        Returns:
            bool: True if document was updated
        """
        try:
            result = await self._db[collection].update_one(query, update)
            success = result.modified_count > 0
            if success:
                logger.info(f"Successfully updated document in {collection}")
            else:
                logger.debug(f"No document found to update in {collection}")
            return success
        except PyMongoError as e:
            logger.error(f"Error updating document in {collection}: {str(e)}")
            raise

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """Delete a single document matching the query.
        
        Args:
            collection (str): Collection name
            query (Dict): Query filter
            
        Returns:
            bool: True if document was deleted
        """
        try:
            result = await self._db[collection].delete_one(query)
            success = result.deleted_count > 0
            if success:
                logger.info(f"Successfully deleted document from {collection}")
            else:
                logger.debug(f"No document found to delete in {collection}")
            return success
        except PyMongoError as e:
            logger.error(f"Error deleting document from {collection}: {str(e)}")
            raise

    async def drop_collection(self, collection: str) -> None:
        """Drop an entire collection.
        
        Args:
            collection (str): Collection name to drop
        """
        try:
            await self._db[collection].drop()
            logger.info(f"Successfully dropped collection: {collection}")
        except PyMongoError as e:
            logger.error(f"Error dropping collection {collection}: {str(e)}")
            raise

    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching the query.
        
        Args:
            collection (str): Collection name
            query (Dict): Query filter
            
        Returns:
            int: Number of matching documents
        """
        try:
            count = await self._db[collection].count_documents(query)
            logger.debug(f"Found {count} documents in {collection} matching query")
            return count
        except PyMongoError as e:
            logger.error(f"Error counting documents in {collection}: {str(e)}")
            raise

    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents into a collection."""
        try:
            result = await self._db[collection].insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except PyMongoError as e:
            logger.error(f"Error inserting documents into {collection}: {e}")
            raise

    async def update_many(self, collection: str, query: Dict[str, Any], 
                         update_data: Dict[str, Any]) -> int:
        """Update multiple documents in a collection."""
        try:
            result = await self._db[collection].update_many(
                query, {'$set': update_data}
            )
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"Error updating documents in {collection}: {e}")
            raise

    async def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents from a collection."""
        try:
            result = await self._db[collection].delete_many(query)
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Error deleting documents from {collection}: {e}")
            raise 