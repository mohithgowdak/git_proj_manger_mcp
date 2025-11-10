"""Resource cache for caching GitHub resources."""

from typing import Optional, List, Dict, Any, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
from ...domain.resource_types import ResourceType, ResourceStatus, Resource


T = TypeVar('T', bound=Resource)


@dataclass
class ResourceCacheOptions:
    """Resource cache options."""
    ttl: Optional[int] = None  # Time to live in milliseconds
    tags: List[str] = field(default_factory=list)
    namespaces: List[str] = field(default_factory=list)
    include_deleted: bool = False


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry."""
    value: T
    expires_at: Optional[float] = None  # Unix timestamp
    tags: List[str] = field(default_factory=list)
    namespace: Optional[str] = None
    last_modified: Optional[str] = None
    version: Optional[int] = None


class ResourceCache:
    """Resource cache for caching GitHub resources."""
    
    _instance: Optional['ResourceCache'] = None
    
    def __init__(self):
        """Initialize resource cache."""
        if ResourceCache._instance is not None:
            raise RuntimeError("ResourceCache is a singleton. Use get_instance() instead.")
        self._cache: Dict[str, CacheEntry[Any]] = {}
        self._default_ttl = 3600000  # 1 hour in milliseconds
        self._tag_index: Dict[str, set] = {}
        self._type_index: Dict[ResourceType, set] = {}
        self._namespace_index: Dict[str, set] = {}
    
    @classmethod
    def get_instance(cls) -> 'ResourceCache':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init__()
        return cls._instance
    
    def _get_cache_key(self, resource_type: ResourceType, resource_id: str) -> str:
        """Get cache key for resource."""
        return f"{resource_type.value}:{resource_id}"
    
    def _parse_cache_key(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Parse cache key to extract type and ID."""
        parts = cache_key.split(':', 1)
        if len(parts) != 2:
            return None
        try:
            resource_type = ResourceType(parts[0])
            return {'type': resource_type, 'id': parts[1]}
        except ValueError:
            return None
    
    async def set(
        self,
        resource_type: ResourceType,
        resource_id: str,
        value: T,
        options: Optional[ResourceCacheOptions] = None
    ) -> None:
        """Set resource with type information for persistence."""
        if options is None:
            options = ResourceCacheOptions()
        
        ttl = options.ttl or self._default_ttl
        expires_at = (time.time() * 1000) + ttl
        tags = options.tags or []
        namespaces = options.namespaces or []
        
        # Cache the resource
        entry: CacheEntry[T] = CacheEntry(
            value=value,
            expires_at=expires_at,
            tags=tags,
            last_modified=getattr(value, 'updated_at', None) or datetime.now().isoformat(),
            version=getattr(value, 'version', None) or 1
        )
        
        cache_key = self._get_cache_key(resource_type, resource_id)
        self._cache[cache_key] = entry
        
        # Index by type
        if resource_type not in self._type_index:
            self._type_index[resource_type] = set()
        self._type_index[resource_type].add(cache_key)
        
        # Index by tags
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(cache_key)
        
        # Index by namespaces
        for namespace in namespaces:
            if namespace not in self._namespace_index:
                self._namespace_index[namespace] = set()
            self._namespace_index[namespace].add(cache_key)
    
    async def get(
        self,
        resource_type: ResourceType,
        resource_id: str,
        options: Optional[ResourceCacheOptions] = None
    ) -> Optional[T]:
        """Get resource by type and ID."""
        if options is None:
            options = ResourceCacheOptions()
        
        cache_key = self._get_cache_key(resource_type, resource_id)
        entry = self._cache.get(cache_key)
        
        if not entry:
            return None
        
        # Check if expired
        if entry.expires_at and (time.time() * 1000) > entry.expires_at:
            self._remove_from_indices(cache_key, entry)
            del self._cache[cache_key]
            return None
        
        # Check if deleted and if we should include deleted resources
        if not options.include_deleted and self._is_deleted(entry.value):
            return None
        
        # Check if it matches the required tags
        if options.tags:
            if not self._has_matching_tags(entry, options.tags):
                return None
        
        return entry.value
    
    async def get_by_type(
        self,
        resource_type: ResourceType,
        options: Optional[ResourceCacheOptions] = None
    ) -> List[T]:
        """Get resources by type."""
        if options is None:
            options = ResourceCacheOptions()
        
        cache_keys = self._type_index.get(resource_type, set())
        if not cache_keys:
            return []
        
        resources: List[T] = []
        for cache_key in cache_keys:
            parsed = self._parse_cache_key(cache_key)
            if parsed:
                resource = await self.get(parsed['type'], parsed['id'], options)
                if resource:
                    resources.append(resource)
        
        return resources
    
    async def get_by_tag(
        self,
        tag: str,
        resource_type: Optional[ResourceType] = None,
        options: Optional[ResourceCacheOptions] = None
    ) -> List[T]:
        """Get resources by tag."""
        if options is None:
            options = ResourceCacheOptions()
        
        cache_keys = self._tag_index.get(tag, set())
        if not cache_keys:
            return []
        
        resources: List[T] = []
        for cache_key in cache_keys:
            parsed = self._parse_cache_key(cache_key)
            if parsed:
                resource = await self.get(parsed['type'], parsed['id'], options)
                if resource and (not resource_type or resource.type == resource_type):
                    resources.append(resource)
        
        return resources
    
    async def get_by_namespace(
        self,
        namespace: str,
        options: Optional[ResourceCacheOptions] = None
    ) -> List[T]:
        """Get resources by namespace."""
        if options is None:
            options = ResourceCacheOptions()
        
        cache_keys = self._namespace_index.get(namespace, set())
        if not cache_keys:
            return []
        
        resources: List[T] = []
        for cache_key in cache_keys:
            parsed = self._parse_cache_key(cache_key)
            if parsed:
                resource = await self.get(parsed['type'], parsed['id'], options)
                if resource:
                    resources.append(resource)
        
        return resources
    
    async def delete(self, resource_type: ResourceType, resource_id: str) -> None:
        """Delete resource from cache."""
        cache_key = self._get_cache_key(resource_type, resource_id)
        entry = self._cache.get(cache_key)
        if entry:
            self._remove_from_indices(cache_key, entry)
            del self._cache[cache_key]
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._tag_index.clear()
        self._type_index.clear()
        self._namespace_index.clear()
    
    def _remove_from_indices(self, cache_key: str, entry: CacheEntry[Any]) -> None:
        """Remove entry from all indices."""
        # Remove from tag index
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(cache_key)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
        
        # Remove from namespace index
        if entry.namespace and entry.namespace in self._namespace_index:
            self._namespace_index[entry.namespace].discard(cache_key)
            if not self._namespace_index[entry.namespace]:
                del self._namespace_index[entry.namespace]
        
        # Remove from type index
        parsed = self._parse_cache_key(cache_key)
        if parsed:
            resource_type = parsed['type']
            if resource_type in self._type_index:
                self._type_index[resource_type].discard(cache_key)
                if not self._type_index[resource_type]:
                    del self._type_index[resource_type]
    
    def _is_deleted(self, resource: Resource) -> bool:
        """Check if resource is deleted."""
        return resource.status == ResourceStatus.DELETED
    
    def _has_matching_tags(self, entry: CacheEntry[Any], required_tags: List[str]) -> bool:
        """Check if entry has matching tags."""
        return all(tag in entry.tags for tag in required_tags)




