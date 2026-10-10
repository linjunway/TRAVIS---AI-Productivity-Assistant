from collections import OrderedDict
from typing import Optional, Union

class LRUCache:
    """
    An LRU (Least Recently Used) Cache implementation with O(1) get and put 
operations.
    
    This implementation uses an OrderedDict to maintain insertion order and allows
    for efficient removal of the least recently used items. The cache maintains a
    fixed maximum capacity, and when full, removes the least recently used item
    before adding a new one.
    
    Args:
        capacity (int): The maximum number of items the cache can hold
        
    Example:
        >>> cache = LRUCache(2)
        >>> cache.put(1, 1)
        >>> cache.put(2, 2)
        >>> cache.get(1)
        1
        >>> cache.put(3, 3)  # Evicts key 2
        >>> cache.get(2)
        -1
    """
    
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: Union[int, str]) -> int:
        """
        Get the value of the key if it exists in the cache, otherwise return -1.
        
        Moves the accessed key to the end (most recently used position).
        
        Args:
            key: The key to look up
            
        Returns:
            The value associated with the key, or -1 if not found
        """
        if key not in self.cache:
            return -1
        
        # Move key to end (mark as most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: Union[int, str], value: int) -> None:
        """
        Insert or update the value of the key in the cache.
        
        If the key already exists, update its value and move it to the end.
        If the key doesn't exist and cache is at capacity, remove the least
        recently used item before inserting the new one.
        
        Args:
            key: The key to insert or update
            value: The value to associate with the key
        """
        if key in self.cache:
            # Update existing key
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            # Remove least recently used item (first item)
            self.cache.popitem(last=False)
        
        self.cache[key] = value


# pytest tests
def test_lru_cache_basic_operations():
    """Test basic get and put operations"""
    cache = LRUCache(2)
    
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    
    cache.put(3, 3)  # Evicts key 2
    assert cache.get(2) == -1
    
    cache.put(4, 4)  # Evicts key 1
    assert cache.get(1) == -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4


def test_lru_cache_update_existing_key():
    """Test that updating an existing key moves it to the end"""
    cache = LRUCache(3)
    
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(3, 3)
    
    # Access key 1 to make it most recently used
    assert cache.get(1) == 1
    
    # Add new key, should evict key 2 (least recently used)
    cache.put(4, 4)
    assert cache.get(2) == -1  # Key 2 should be evicted
    assert cache.get(1) == 1   # Key 1 should still exist
    assert cache.get(3) == 3   # Key 3 should still exist
    assert cache.get(4) == 4   # Key 4 should exist


def test_lru_cache_edge_cases():
    """Test edge cases like capacity 1 and invalid operations"""
    # Test with capacity 1
    cache = LRUCache(1)
    cache.put(1, 1)
    assert cache.get(1) == 1
    
    cache.put(2, 2)  # Should evict key 1
    assert cache.get(1) == -1
    assert cache.get(2) == 2
    
    # Test with string keys
    cache = LRUCache(2)
    cache.put("a", 10)
    cache.put("b", 20)
    assert cache.get("a") == 10
    cache.put("c", 30)  # Should evict "b"
    assert cache.get("b") == -1
    assert cache.get("c") == 30


if __name__ == "__main__":
    # Example usage
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    print(cache.get(1))  # returns 1
    cache.put(3, 3)      # evicts key 2
    print(cache.get(2))  # returns -1 (not found)
    cache.put(4, 4)      # evicts key 1
    print(cache.get(1))  # returns -1 (not found)
    print(cache.get(3))  # returns 3
    print(cache.get(4))  # returns 4