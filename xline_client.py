"""Xline client integration for Pinnacle Copilot."""
import os
import json
from typing import Dict, Any, Optional

from xline import XlineClient

class PinnacleXlineClient:
    """Xline client wrapper for Pinnacle Copilot."""
    
    def __init__(self, endpoints: str = "http://127.0.0.1:2379"):
        """Initialize the Xline client.
        
        Args:
            endpoints: Comma-separated list of Xline server endpoints
        """
        self.client = XlineClient(endpoints.split(','))
        self.namespace = "pinnacle/"
        
    async def put(self, key: str, value: Any) -> bool:
        """Store a key-value pair in Xline.
        
        Args:
            key: The key to store
            value: The value to store (will be JSON serialized)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value)
            await self.client.put(f"{self.namespace}{key}", serialized)
            return True
        except Exception as e:
            print(f"Error storing key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key from Xline.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The deserialized value, or None if not found
        """
        try:
            result = await self.client.get(f"{self.namespace}{key}")
            if result and result.kvs:
                return json.loads(result.kvs[0].value)
            return None
        except Exception as e:
            print(f"Error retrieving key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Xline.
        
        Args:
            key: The key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.client.delete(f"{self.namespace}{key}")
            return True
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False
    
    async def list_keys(self, prefix: str = "") -> list:
        """List all keys with the given prefix.
        
        Args:
            prefix: The prefix to filter keys by
            
        Returns:
            List of matching keys
        """
        try:
            result = await self.client.get(
                f"{self.namespace}{prefix}", 
                prefix=True
            )
            return [kv.key.decode() for kv in result.kvs] if result.kvs else []
        except Exception as e:
            print(f"Error listing keys with prefix {prefix}: {e}")
            return []

# Example usage
async def example_usage():
    """Example usage of the PinnacleXlineClient."""
    client = PinnacleXlineClient()
    
    # Store data
    await client.put("config/server", {"host": "localhost", "port": 8000})
    
    # Retrieve data
    config = await client.get("config/server")
    print(f"Server config: {config}")
    
    # List keys
    keys = await client.list_keys("config/")
    print(f"Config keys: {keys}")
    
    # Delete data
    await client.delete("config/server")
