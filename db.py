"""In-memory database implementation using cachetools."""

import functools
from cachetools import LRUCache
from typing import Dict, List, Optional, Type, TypeVar, Generic
from uuid import UUID

from core.logger import logger
from models import ChangelogEntry, Tag, User


T = TypeVar('T')


class Database(Generic[T]):
    """
    In-memory database using LRUCache.

    Parameters
    ----------
    model_class : Type
        The model class this database stores
    cache_size : int, optional
        Size of the LRU cache, by default 1000
    """

    def __init__(self, model_class: Type[T], cache_size: int = 1000):
        """
        Initialize database with specified model class and cache size.

        Parameters
        ----------
        model_class : Type[T]
            Model class to store
        cache_size : int, optional
            Size of the LRU cache, by default 1000
        """
        self.model_class = model_class
        self.cache = LRUCache(maxsize=cache_size)
        self._name = model_class.__name__
        logger.info(f"Initialized {self._name} database with cache size {cache_size}")

    def get(self, id: UUID) -> Optional[T]:
        """
        Get an item by ID.

        Parameters
        ----------
        id : UUID
            Item ID

        Returns
        -------
        Optional[T]
            Found item or None
        """
        return self.cache.get(str(id))

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
        self.cache[str(item.id)] = item
        logger.debug(f"Created {self._name} with ID {item.id}")
        return item

    def update(self, id: UUID, item: T) -> Optional[T]:
        """
        Update an existing item.

        Parameters
        ----------
        id : UUID
            Item ID
        item : T
            Updated item

        Returns
        -------
        Optional[T]
            Updated item or None if not found
        """
        if str(id) in self.cache:
            self.cache[str(id)] = item
            logger.debug(f"Updated {self._name} with ID {id}")
            return item
        return None

    def delete(self, id: UUID) -> bool:
        """
        Delete an item by ID.

        Parameters
        ----------
        id : UUID
            Item ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        if str(id) in self.cache:
            del self.cache[str(id)]
            logger.debug(f"Deleted {self._name} with ID {id}")
            return True
        return False

    def list_all(self) -> List[T]:
        """
        List all items.

        Returns
        -------
        List[T]
            List of all items
        """
        return list(self.cache.values())

    def find_by(self, field: str, value) -> List[T]:
        """
        Find items by field value.

        Parameters
        ----------
        field : str
            Field name to search
        value : Any
            Value to search for

        Returns
        -------
        List[T]
            List of matching items
        """
        return [item for item in self.cache.values() if getattr(item, field) == value]


# Initialize databases
user_db = Database[User](User)
tag_db = Database[Tag](Tag)
changelog_db = Database[ChangelogEntry](ChangelogEntry)


