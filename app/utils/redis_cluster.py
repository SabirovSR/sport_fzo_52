import asyncio
from typing import Optional, List, Any
import redis.asyncio as redis
from rediscluster import RedisCluster
from loguru import logger
from app.config import settings


class RedisClusterManager:
    def __init__(self):
        self.cluster_client: Optional[RedisCluster] = None
        self.single_client: Optional[redis.Redis] = None
        self.is_cluster_mode = False

    async def initialize(self):
        """Initialize Redis connection (cluster or single)"""
        try:
            # Try cluster mode first
            await self._init_cluster()
        except Exception as e:
            logger.warning(f"Redis cluster initialization failed: {e}")
            logger.info("Falling back to single Redis instance")
            await self._init_single()

    async def _init_cluster(self):
        """Initialize Redis cluster"""
        cluster_nodes = [
            {"host": "redis-node-1", "port": 7001},
            {"host": "redis-node-2", "port": 7002},
            {"host": "redis-node-3", "port": 7003},
            {"host": "redis-node-4", "port": 7004},
            {"host": "redis-node-5", "port": 7005},
            {"host": "redis-node-6", "port": 7006},
        ]

        self.cluster_client = RedisCluster(
            startup_nodes=cluster_nodes,
            decode_responses=True,
            password=settings.REDIS_PASSWORD,
            skip_full_coverage_check=True,
            health_check_interval=30,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        # Test cluster connection
        await self.cluster_client.ping()
        self.is_cluster_mode = True
        logger.info("Redis cluster initialized successfully")

    async def _init_single(self):
        """Initialize single Redis instance"""
        redis_url = settings.redis_url
        self.single_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )

        # Test single connection
        await self.single_client.ping()
        self.is_cluster_mode = False
        logger.info("Single Redis instance initialized successfully")

    async def get_client(self):
        """Get Redis client (cluster or single)"""
        if self.is_cluster_mode and self.cluster_client:
            return self.cluster_client
        elif self.single_client:
            return self.single_client
        else:
            raise Exception("Redis not initialized")

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set key-value with optional expiration"""
        try:
            client = await self.get_client()
            if ex:
                return await client.setex(key, ex, value)
            else:
                return await client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def incr(self, key: str) -> Optional[int]:
        """Increment key value"""
        try:
            client = await self.get_client()
            return await client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            client = await self.get_client()
            return await client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            client = await self.get_client()
            return await client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    async def keys(self, pattern: str) -> List[str]:
        """Get keys by pattern"""
        try:
            client = await self.get_client()
            if self.is_cluster_mode:
                # In cluster mode, we need to scan all nodes
                all_keys = []
                for node in self.cluster_client.get_nodes():
                    node_keys = await node.keys(pattern)
                    all_keys.extend(node_keys)
                return all_keys
            else:
                return await client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []

    async def flushdb(self) -> bool:
        """Flush database"""
        try:
            client = await self.get_client()
            if self.is_cluster_mode:
                # In cluster mode, flush all nodes
                for node in self.cluster_client.get_nodes():
                    await node.flushdb()
            else:
                await client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False

    async def info(self) -> dict:
        """Get Redis info"""
        try:
            client = await self.get_client()
            if self.is_cluster_mode:
                # Get info from all nodes
                cluster_info = {}
                for i, node in enumerate(self.cluster_client.get_nodes()):
                    node_info = await node.info()
                    cluster_info[f"node_{i+1}"] = {
                        "host": node.host,
                        "port": node.port,
                        "role": node_info.get("role", "unknown"),
                        "connected_clients": node_info.get("connected_clients", 0),
                        "used_memory": node_info.get("used_memory", 0),
                        "uptime_in_seconds": node_info.get("uptime_in_seconds", 0)
                    }
                return cluster_info
            else:
                info = await client.info()
                return {
                    "single_node": {
                        "role": info.get("role", "master"),
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory": info.get("used_memory", 0),
                        "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                    }
                }
        except Exception as e:
            logger.error(f"Redis INFO error: {e}")
            return {}

    async def health_check(self) -> dict:
        """Check Redis health"""
        try:
            client = await self.get_client()
            
            if self.is_cluster_mode:
                # Check cluster health
                cluster_info = await client.cluster_info()
                nodes_info = []
                
                for node in self.cluster_client.get_nodes():
                    try:
                        await node.ping()
                        node_info = await node.info()
                        nodes_info.append({
                            "host": node.host,
                            "port": node.port,
                            "status": "healthy",
                            "role": node_info.get("role", "unknown"),
                            "uptime": node_info.get("uptime_in_seconds", 0)
                        })
                    except Exception as e:
                        nodes_info.append({
                            "host": node.host,
                            "port": node.port,
                            "status": "unhealthy",
                            "error": str(e)
                        })
                
                return {
                    "mode": "cluster",
                    "status": "healthy" if cluster_info.get("cluster_state") == "ok" else "degraded",
                    "cluster_state": cluster_info.get("cluster_state"),
                    "nodes": nodes_info
                }
            else:
                # Check single instance
                await client.ping()
                info = await client.info()
                
                return {
                    "mode": "single",
                    "status": "healthy",
                    "uptime": info.get("uptime_in_seconds", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory", 0)
                }
                
        except Exception as e:
            return {
                "mode": "cluster" if self.is_cluster_mode else "single",
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self):
        """Close connections"""
        try:
            if self.cluster_client:
                await self.cluster_client.close()
            if self.single_client:
                await self.single_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")


# Global Redis manager instance
redis_manager = RedisClusterManager()