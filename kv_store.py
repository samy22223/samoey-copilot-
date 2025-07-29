"""
Key-Value Store Client

This module provides a simple interface to a key-value store using etcd3.
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import etcd3

class KeyValueStore:
    """A simple key-value store client using etcd3."""
    
    def __init__(self, host: str = 'localhost', port: int = 2379):
        """Initialize the key-value store client.
        
        Args:
            host: The hostname of the etcd server.
            port: The port of the etcd server.
        """
        self.client = etcd3.client(host=host, port=port)
        
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a key-value pair in the store.
        
        Args:
            key: The key to store the value under.
            value: The value to store (will be JSON-serialized).
            ttl: Optional time-to-live in seconds.
            
        Returns:
            bool: True if the operation was successful.
        """
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            lease = self.client.lease(ttl) if ttl else None
            self.client.put(key, serialized_value, lease=lease)
            return True
        except Exception as e:
            print(f"Error putting key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the store by key.
        
        Args:
            key: The key to retrieve the value for.
            
        Returns:
            The deserialized value, or None if the key doesn't exist.
        """
        try:
            value, _ = self.client.get(key)
            if value is not None:
                return json.loads(value.decode('utf-8'))
            return None
        except Exception as e:
            print(f"Error getting key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair from the store.
        
        Args:
            key: The key to delete.
            
        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        try:
            return self.client.delete(key)
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False
    
    def list_keys(self, prefix: str = '') -> List[str]:
        """List all keys in the store with the given prefix.
        
        Args:
            prefix: Optional prefix to filter keys.
            
        Returns:
            A list of keys that match the prefix.
        """
        try:
            return [metadata.key.decode('utf-8') 
                   for _, metadata in self.client.get_prefix(prefix)]
        except Exception as e:
            print(f"Error listing keys with prefix {prefix}: {e}")
            return []
    
    def watch(self, key: str, callback: callable) -> None:
        """Watch for changes to a key and call the callback when it changes.
        
        Args:
            key: The key to watch.
            callback: A function to call when the key changes.
                     The function should accept a single argument (the new value).
        """
        def watch_callback(event):
            if event.events:
                for event in event.events:
                    if event.type == etcd3.events.PUT_EVENT:
                        try:
                            value = json.loads(event.value.decode('utf-8'))
                            callback(value)
                        except Exception as e:
                            print(f"Error in watch callback: {e}")
        
        self.client.add_watch_callback(key, watch_callback)

# Singleton instance
kv_store = KeyValueStore()
