"""MongoDB database implementation using pymongo."""

from typing import Dict, List, Optional, Type, TypeVar, Generic, Any

import pymongo
from bson import ObjectId
from pydantic import BaseModel

from core.config import get_settings
from core.logger import logger
from models import PyObjectId

settings = get_settings()

T = TypeVar('T', bound=BaseModel)

class MongoDB(Generic[T]):
    """
    MongoDB database implementation.

    Parameters
    ----------
    model_class : Type[T]
        The model class this database stores
    collection_name : str
        Name of the MongoDB collection
    """

    def __init__(self, model_class: Type[T], collection_name: str):
        """
        Initialize MongoDB connection.

        Parameters
        ----------
        model_class : Type[T]
            Model class to store
        collection_name : str
            Name of the MongoDB collection
        """
        self.model_class = model_class
        self.collection_name = collection_name
        self._name = model_class.__name__

        mongo_uri = settings.mongodb_uri

        if not mongo_uri:
            raise ValueError("MongoDB URI is not set in the environment variables.")

        self.client = pymongo.MongoClient(mongo_uri)

        try:
            self.client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")

        self.db = self.client[settings.mongodb_name]
        self.collection = self.db[collection_name]
        
        logger.info(f"Connected to MongoDB collection '{collection_name}'")
    
    def _convert_id(self, item: Dict) -> Dict:
        """
        Convert MongoDB ObjectId to string ID for Pydantic.
        """
        if item is None:
            return item
        if "_id" in item:
            item["id"] = str(item["_id"])
        return item

    def _prepare_for_mongo(self, item: T) -> Dict:
        """
        Prepare item for MongoDB storage, converting id to _id and handling ObjectIds.
        """
        data = item.model_dump(by_alias=True, exclude_none=True)

        # Convert id to _id for MongoDB
        if "id" in data:
            # If id is a string, convert to ObjectId
            id_value = data.pop("id")
            if isinstance(id_value, str):
                try:
                    data["_id"] = ObjectId(id_value)
                except:
                    data["_id"] = id_value
            else:
                data["_id"] = id_value

        # Ensure other *_id fields are also ObjectIds
        for key, value in data.items():
            if key == "_id" or key == "user_id" or key.endswith("_id"):
                if isinstance(value, str):
                    try:
                        data[key] = ObjectId(value)
                    except:
                        pass
            elif isinstance(value, list) and value and key == "tags":
                # Handle arrays of IDs (like tags)
                try:
                    data[key] = [
                        ObjectId(x) if isinstance(x, str) else x for x in value
                    ]
                except:
                    pass

        return data

    def get(self, id: PyObjectId) -> Optional[T]:
        """
        Get an item by ID.
        """
        if not isinstance(id, ObjectId):
            try:
                id = ObjectId(str(id))
            except:
                logger.error(f"Invalid ObjectId: {id}")
                return None

        result = self.collection.find_one({"_id": id})
        if result:
            return self.model_class.model_validate(result)
        return None
    
    def create(self, item: T) -> T:
        """
        Create a new item.

        Parameters
        ----------
        item : T
            Item to create

        Returns
        -------
        T
            Created item
        """
        data = self._prepare_for_mongo(item)
        result = self.collection.insert_one(data)
        item.id = result.inserted_id
        return item
    
    def update(self, id: PyObjectId, item: T) -> Optional[T]:
        """
        Update an existing item.

        Parameters
        ----------
        id : PyObjectId
            Item ID
        item : T
            Updated item

        Returns
        -------
        Optional[T]
            Updated item or None if not found
        """
        data = self._prepare_for_mongo(item)
        result = self.collection.update_one({"_id": ObjectId(str(id))}, {"$set": data})
        
        if result.matched_count > 0:
            return item
        return None
    
    def delete(self, id: PyObjectId) -> bool:
        """
        Delete an item by ID.

        Parameters
        ----------
        id : PyObjectId
            Item ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        result = self.collection.delete_one({"_id": ObjectId(str(id))})
        return result.deleted_count > 0
    
    def list_all(self) -> List[T]:
        """
        List all items.

        Returns
        -------
        List[T]
            List of all items
        """
        results = self.collection.find()
        items = [self.model_class.model_validate(self._convert_id(item)) for item in results]
        return items

    def find_by(self, field: str, value: Any) -> List[T]:
        """
        Find items by field value.
        """
        # Convert to ObjectId if searching by ID fields
        if field == "_id" or field == "user_id" or field.endswith("_id"):
            if isinstance(value, str):
                try:
                    value = ObjectId(value)
                except:
                    logger.error(f"Invalid ObjectId: {value}")
                    return []
            elif isinstance(value, PyObjectId):
                value = ObjectId(str(value))

        results = list(self.collection.find({field: value}))
        items = [self.model_class.model_validate(item) for item in results]
        return items
    
    def find_with_pagination(self, query: Dict, skip: int = 0, limit: int = 10) -> List[T]:
        """
        Find items with pagination.
        
        Parameters
        ----------
        query : Dict
            MongoDB query
        skip : int, optional
            Number of documents to skip, by default 0
        limit : int, optional
            Maximum number of documents to return, by default 10
            
        Returns
        -------
        List[T]
            List of matching items
        """
        results = self.collection.find(query).skip(skip).limit(limit)
        items = [self.model_class.model_validate(self._convert_id(item)) for item in results]
        return items
    
    def count(self, query: Dict = None) -> int:
        """
        Count documents matching a query.
        
        Parameters
        ----------
        query : Dict, optional
            MongoDB query, by default None (count all)
            
        Returns
        -------
        int
            Document count
        """
        if query is None:
            query = {}
        return self.collection.count_documents(query)
    
    def clear_collection(self) -> None:
        """
        Clear the entire collection.
        
        Warning: Use with caution! This deletes all documents in the collection.
        """
        self.collection.delete_many({})
        logger.warning(f"Cleared all documents from collection {self.collection_name}")

from models import User, Tag, ChangelogEntry

user_db = MongoDB(User, "users")
tag_db = MongoDB(Tag, "tags")
changelog_db = MongoDB(ChangelogEntry, "changelog_entries")