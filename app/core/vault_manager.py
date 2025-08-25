"""
Vault Secrets Manager for Samoey Copilot
Enterprise-grade secrets management with HashiCorp Vault integration
"""

import os
import json
import asyncio
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import hvac
from prometheus_client import Counter, Histogram
import aioredis

logger = logging.getLogger(__name__)

# Metrics
VAULT_OPERATIONS = Counter('vault_operations_total', 'Total Vault operations', ['operation', 'status'])
SECRET_FETCH_TIME = Histogram('secret_fetch_duration_seconds', 'Secret fetch duration')
SECRET_REFRESH_COUNT = Counter('secret_refresh_total', 'Total secret refresh events', ['secret_type'])

class VaultManager:
    """Enterprise-grade secrets management using HashiCorp Vault"""

    def __init__(self):
        self.client: Optional[hvac.Client] = None
        self.redis: Optional[aioredis.Redis] = None
        self.token: Optional[str] = None
        self.secrets_cache: Dict[str, Dict] = {}
        self.last_refresh: Dict[str, datetime] = {}
        self.cache_ttl = int(os.getenv('VAULT_CACHE_TTL', '300'))  # 5 minutes default

    async def initialize(self, redis_client: aioredis.Redis = None):
        """Initialize Vault manager with Redis for caching"""
        self.redis = redis_client

        # Vault configuration
        vault_url = os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.token = os.getenv('VAULT_TOKEN')

        if not self.token:
            logger.warning("VAULT_TOKEN not set, secrets management will be limited")
            return

        try:
            # Initialize Vault client
            self.client = hvac.Client(url=vault_url, token=self.token)

            # Verify Vault connection
            if not self.client.is_authenticated():
                logger.error("Failed to authenticate with Vault")
                return False

            logger.info("✅ Vault manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Vault manager: {e}")
            return False

    async def get_secret(self, path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieve secret from Vault with caching"""
        if not self.client:
            logger.warning("Vault client not initialized")
            return None

        start_time = asyncio.get_event_loop().time()

        # Check cache first
        if use_cache and path in self.secrets_cache:
            cache_age = (datetime.utcnow() - self.last_refresh[path]).total_seconds()
            if cache_age < self.cache_ttl:
                logger.debug(f"Returning cached secret for {path}")
                return self.secrets_cache[path]

        try:
            # Fetch secret from Vault
            with SECRET_FETCH_TIME.time():
                response = self.client.secrets.kv.v2.read_secret_version(path=path)

            if response and 'data' in response and 'data' in response['data']:
                secret_data = response['data']['data']

                # Update cache
                self.secrets_cache[path] = secret_data
                self.last_refresh[path] = datetime.utcnow()

                # Store in Redis for cross-process caching
                if self.redis:
                    await self.redis.setex(
                        f'vault:secret:{path}',
                        self.cache_ttl,
                        json.dumps(secret_data)
                    )

                VAULT_OPERATIONS.labels(operation='get_secret', status='success').inc()
                logger.debug(f"Successfully retrieved secret for {path}")
                return secret_data
            else:
                logger.warning(f"No data found for secret path: {path}")
                VAULT_OPERATIONS.labels(operation='get_secret', status='not_found').inc()
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve secret {path}: {e}")
            VAULT_OPERATIONS.labels(operation='get_secret', status='error').inc()

            # Try to return cached data if available
            if path in self.secrets_cache:
                logger.warning(f"Returning stale cached data for {path}")
                return self.secrets_cache[path]

            return None

    async def create_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Create or update secret in Vault"""
        if not self.client:
            logger.warning("Vault client not initialized")
            return False

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data
            )

            # Update cache
            self.secrets_cache[path] = data
            self.last_refresh[path] = datetime.utcnow()

            # Invalidate Redis cache
            if self.redis:
                await self.redis.delete(f'vault:secret:{path}')

            VAULT_OPERATIONS.labels(operation='create_secret', status='success').inc()
            logger.info(f"Successfully created secret at {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create secret {path}: {e}")
            VAULT_OPERATIONS.labels(operation='create_secret', status='error').inc()
            return False

    async def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault"""
        if not self.client:
            logger.warning("Vault client not initialized")
            return False

        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)

            # Remove from cache
            self.secrets_cache.pop(path, None)
            self.last_refresh.pop(path, None)

            # Invalidate Redis cache
            if self.redis:
                await self.redis.delete(f'vault:secret:{path}')

            VAULT_OPERATIONS.labels(operation='delete_secret', status='success').inc()
            logger.info(f"Successfully deleted secret at {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            VAULT_OPERATIONS.labels(operation='delete_secret', status='error').inc()
            return False

    async def list_secrets(self, path: str = "") -> List[str]:
        """List secrets at a given path"""
        if not self.client:
            logger.warning("Vault client not initialized")
            return []

        try:
            response = self.client.secrets.kv.v2.list_secrets(path=path)
            if response and 'data' in response and 'keys' in response['data']:
                return response['data']['keys']
            return []

        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            return []

    async def generate_database_credentials(self, role: str) -> Optional[Dict[str, str]]:
        """Generate dynamic database credentials"""
        if not self.client:
            logger.warning("Vault client not initialized")
            return None

        try:
            response = self.client.secrets.database.generate_credentials(
                name=role
            )

            if response and 'data' in response:
                credentials = response['data']
                VAULT_OPERATIONS.labels(operation='generate_db_creds', status='success').inc()
                logger.info(f"Generated database credentials for role: {role}")
                return credentials
            else:
                logger.error(f"Failed to generate database credentials for role: {role}")
                return None

        except Exception as e:
            logger.error(f"Failed to generate database credentials: {e}")
            VAULT_OPERATIONS.labels(operation='generate_db_creds', status='error').inc()
            return None

    async def generate_certificate(self, common_name: str, ttl: str = "24h") -> Optional[Dict[str, str]]:
        """Generate TLS certificate using PKI"""
        if not self.client:
            logger.warning("Vault client not initialized")
            return None

        try:
            response = self.client.secrets.pki.issue_certificate(
                name='samoey-internal',
                common_name=common_name,
                ttl=ttl
            )

            if response and 'data' in response:
                cert_data = response['data']
                VAULT_OPERATIONS.labels(operation='generate_cert', status='success').inc()
                logger.info(f"Generated certificate for {common_name}")
                return cert_data
            else:
                logger.error(f"Failed to generate certificate for {common_name}")
                return None

        except Exception as e:
            logger.error(f"Failed to generate certificate: {e}")
            VAULT_OPERATIONS.labels(operation='generate_cert', status='error').inc()
            return None

    async def rotate_secrets(self, secret_paths: List[str]) -> Dict[str, bool]:
        """Rotate multiple secrets"""
        results = {}

        for path in secret_paths:
            try:
                # Get current secret
                current_secret = await self.get_secret(path, use_cache=False)
                if not current_secret:
                    results[path] = False
                    continue

                # Generate new values for sensitive fields
                new_secret = {}
                for key, value in current_secret.items():
                    if 'password' in key.lower() or 'secret' in key.lower() or 'key' in key.lower():
                        # Generate new random value
                        import secrets
                        if 'password' in key.lower():
                            new_secret[key] = secrets.token_urlsafe(32)
                        elif 'key' in key.lower() and len(str(value)) == 64:  # Assume 64-char hex key
                            new_secret[key] = secrets.token_hex(32)
                        else:
                            new_secret[key] = secrets.token_urlsafe(16)
                    else:
                        new_secret[key] = value

                # Update secret
                success = await self.create_secret(path, new_secret)
                results[path] = success

                if success:
                    SECRET_REFRESH_COUNT.labels(secret_type='rotated').inc()
                    logger.info(f"Successfully rotated secret: {path}")
                else:
                    logger.error(f"Failed to rotate secret: {path}")

            except Exception as e:
                logger.error(f"Error rotating secret {path}: {e}")
                results[path] = False

        return results

    async def get_application_secrets(self, environment: str) -> Dict[str, Any]:
        """Get all application secrets for a specific environment"""
        secrets = {}

        # Define secret paths for the environment
        secret_paths = [
            f"{environment}/database",
            f"{environment}/api",
            f"{environment}/monitoring",
            f"{environment}/security"
        ]

        for path in secret_paths:
            secret_data = await self.get_secret(path)
            if secret_data:
                # Add to secrets dict with path as prefix
                path_parts = path.split('/')
                if len(path_parts) >= 2:
                    category = path_parts[1]
                    secrets[category] = secret_data

        return secrets

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Vault integration"""
        health_status = {
            'vault_connected': False,
            'vault_authenticated': False,
            'cache_size': len(self.secrets_cache),
            'last_refresh_times': {},
            'status': 'healthy'
        }

        try:
            if self.client:
                health_status['vault_connected'] = True
                health_status['vault_authenticated'] = self.client.is_authenticated()

                # Test reading a secret
                test_secret = await self.get_secret('health-check', use_cache=False)
                if test_secret is not None:
                    health_status['status'] = 'healthy'
                else:
                    health_status['status'] = 'degraded'
            else:
                health_status['status'] = 'unhealthy'

        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            health_status['status'] = 'unhealthy'

        # Add last refresh times
        for path, refresh_time in self.last_refresh.items():
            health_status['last_refresh_times'][path] = refresh_time.isoformat()

        return health_status

    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        expired_paths = []

        for path, refresh_time in self.last_refresh.items():
            if (current_time - refresh_time).total_seconds() > self.cache_ttl:
                expired_paths.append(path)

        for path in expired_paths:
            self.secrets_cache.pop(path, None)
            self.last_refresh.pop(path, None)

            if self.redis:
                await self.redis.delete(f'vault:secret:{path}')

        if expired_paths:
            logger.info(f"Cleaned up {len(expired_paths)} expired cache entries")

# Global instance
vault_manager = VaultManager()
