"""Event store for storing and querying resource events."""

import os
import json
import gzip
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sys
from ...infrastructure.logger import get_logger


@dataclass
class EventStoreOptions:
    """Event store options."""
    retention_days: int = 30
    max_events_in_memory: int = 10000
    storage_directory: str = ".mcp-cache/events"
    enable_compression: bool = True


@dataclass
class EventQuery:
    """Event query."""
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    event_type: Optional[str] = None
    source: Optional[str] = None
    from_timestamp: Optional[str] = None
    to_timestamp: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass
class EventStoreStats:
    """Event store statistics."""
    total_events: int = 0
    events_in_memory: int = 0
    events_on_disk: int = 0
    oldest_event: Optional[str] = None
    newest_event: Optional[str] = None
    storage_size: int = 0


@dataclass
class ResourceEvent:
    """Resource event."""
    id: str
    type: str
    resource_type: str
    resource_id: str
    source: str
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventStore:
    """Event store for storing and querying resource events."""
    
    def __init__(self, options: Optional[EventStoreOptions] = None):
        """Initialize event store."""
        self._logger = get_logger(self.__class__.__name__)
        
        # Use provided options or defaults
        if options:
            self._options = options
        else:
            try:
                from ...env import EVENT_RETENTION_DAYS, MAX_EVENTS_IN_MEMORY, CACHE_DIRECTORY
                self._options = EventStoreOptions(
                    retention_days=EVENT_RETENTION_DAYS,
                    max_events_in_memory=MAX_EVENTS_IN_MEMORY,
                    storage_directory=os.path.join(CACHE_DIRECTORY, 'events'),
                    enable_compression=True
                )
            except ImportError:
                self._options = EventStoreOptions(
                    retention_days=30,
                    max_events_in_memory=10000,
                    storage_directory=".mcp-cache/events",
                    enable_compression=True
                )
        
        self._events_directory = Path(self._options.storage_directory)
        self._index_file = self._events_directory / 'index.json'
        self._directory_initialized = False
        
        # In-memory event buffer for fast access
        self._memory_buffer: List[ResourceEvent] = []
        self._event_index: Dict[str, int] = {}  # eventId -> buffer index
        
        # File rotation tracking
        self._current_file_date: str = ''
        self._current_file_events: int = 0
        self._max_events_per_file = 10000
    
    async def store_event(self, event: ResourceEvent) -> None:
        """Store a new event."""
        try:
            await self._ensure_directory_exists()
            
            # Add to memory buffer
            self._add_to_memory_buffer(event)
            
            # Persist to disk
            await self._persist_event(event)
            
            self._logger.debug(f"Stored event {event.id} ({event.type} {event.resource_type})")
        except Exception as e:
            self._logger.error(f"Failed to store event {event.id}: {e}")
            raise
    
    async def store_events(self, events: List[ResourceEvent]) -> None:
        """Store multiple events in batch."""
        if not events:
            return
        
        try:
            await self._ensure_directory_exists()
            
            # Add all to memory buffer
            for event in events:
                self._add_to_memory_buffer(event)
            
            # Persist all to disk
            await self._persist_events(events)
            
            self._logger.debug(f"Stored {len(events)} events in batch")
        except Exception as e:
            self._logger.error(f"Failed to store {len(events)} events in batch: {e}")
            raise
    
    async def get_events(self, query: Optional[EventQuery] = None) -> List[ResourceEvent]:
        """Get events by query."""
        if query is None:
            query = EventQuery()
        
        try:
            # First check memory buffer
            events = self._query_memory_buffer(query)
            
            # If we need more events or specific time range, check disk
            if self._needs_disk_query(query, len(events)):
                disk_events = await self._query_disk_events(query)
                events = self._merge_and_deduplicate_events(events, disk_events)
            
            # Apply final filtering and sorting
            events = self._apply_final_filtering(events, query)
            
            self._logger.debug(f"Retrieved {len(events)} events for query")
            return events
        except Exception as e:
            self._logger.error(f"Failed to get events: {e}")
            raise
    
    async def get_events_from_timestamp(self, timestamp: str, limit: Optional[int] = None) -> List[ResourceEvent]:
        """Get events from a specific timestamp (for replay)."""
        return await self.get_events(EventQuery(
            from_timestamp=timestamp,
            limit=limit or 1000
        ))
    
    async def get_recent_events(self, limit: int = 100) -> List[ResourceEvent]:
        """Get recent events."""
        events = sorted(self._memory_buffer, key=lambda e: e.timestamp, reverse=True)[:limit]
        return events
    
    async def cleanup(self) -> None:
        """Clean up old events based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self._options.retention_days)
            cutoff_timestamp = cutoff_date.isoformat()
            
            # Clean memory buffer
            initial_memory_size = len(self._memory_buffer)
            self._memory_buffer = [e for e in self._memory_buffer if e.timestamp >= cutoff_timestamp]
            self._rebuild_event_index()
            
            # Clean disk files
            deleted_files = await self._cleanup_disk_files(cutoff_date)
            
            self._logger.info(f"Cleanup completed: removed {initial_memory_size - len(self._memory_buffer)} events from memory, {deleted_files} files from disk")
        except Exception as e:
            self._logger.error(f"Failed to cleanup events: {e}")
    
    async def get_stats(self) -> EventStoreStats:
        """Get event store statistics."""
        try:
            disk_stats = await self._get_disk_stats()
            
            stats = EventStoreStats(
                total_events=len(self._memory_buffer) + disk_stats.get('event_count', 0),
                events_in_memory=len(self._memory_buffer),
                events_on_disk=disk_stats.get('event_count', 0),
                storage_size=disk_stats.get('total_size', 0)
            )
            
            if self._memory_buffer:
                sorted_events = sorted(self._memory_buffer, key=lambda e: e.timestamp)
                stats.oldest_event = sorted_events[0].timestamp
                stats.newest_event = sorted_events[-1].timestamp
            
            return stats
        except Exception as e:
            self._logger.error(f"Failed to get event store stats: {e}")
            raise
    
    async def _ensure_directory_exists(self) -> None:
        """Ensure events directory exists."""
        if not self._directory_initialized:
            self._events_directory.mkdir(parents=True, exist_ok=True)
            self._directory_initialized = True
    
    def _add_to_memory_buffer(self, event: ResourceEvent) -> None:
        """Add event to memory buffer."""
        # Remove oldest events if buffer is full
        while len(self._memory_buffer) >= self._options.max_events_in_memory:
            oldest_event = self._memory_buffer.pop(0)
            if oldest_event.id in self._event_index:
                del self._event_index[oldest_event.id]
        
        # Add new event
        self._memory_buffer.append(event)
        self._event_index[event.id] = len(self._memory_buffer) - 1
    
    def _rebuild_event_index(self) -> None:
        """Rebuild event index."""
        self._event_index = {event.id: idx for idx, event in enumerate(self._memory_buffer)}
    
    def _query_memory_buffer(self, query: EventQuery) -> List[ResourceEvent]:
        """Query memory buffer."""
        events = self._memory_buffer
        
        # Apply filters
        if query.resource_type:
            events = [e for e in events if e.resource_type == query.resource_type]
        if query.resource_id:
            events = [e for e in events if e.resource_id == query.resource_id]
        if query.event_type:
            events = [e for e in events if e.type == query.event_type]
        if query.source:
            events = [e for e in events if e.source == query.source]
        if query.from_timestamp:
            events = [e for e in events if e.timestamp >= query.from_timestamp]
        if query.to_timestamp:
            events = [e for e in events if e.timestamp <= query.to_timestamp]
        
        return events
    
    def _needs_disk_query(self, query: EventQuery, memory_count: int) -> bool:
        """Check if disk query is needed."""
        if query.limit and memory_count >= query.limit:
            return False
        if query.from_timestamp or query.to_timestamp:
            return True
        return False
    
    async def _query_disk_events(self, query: EventQuery) -> List[ResourceEvent]:
        """Query disk events."""
        # Simplified implementation - would need full file reading logic
        return []
    
    def _merge_and_deduplicate_events(self, events1: List[ResourceEvent], events2: List[ResourceEvent]) -> List[ResourceEvent]:
        """Merge and deduplicate events."""
        seen_ids = {e.id for e in events1}
        merged = list(events1)
        
        for event in events2:
            if event.id not in seen_ids:
                merged.append(event)
                seen_ids.add(event.id)
        
        return merged
    
    def _apply_final_filtering(self, events: List[ResourceEvent], query: EventQuery) -> List[ResourceEvent]:
        """Apply final filtering and sorting."""
        # Sort by timestamp descending
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        # Apply limit and offset
        if query.offset:
            events = events[query.offset:]
        if query.limit:
            events = events[:query.limit]
        
        return events
    
    async def _persist_event(self, event: ResourceEvent) -> None:
        """Persist event to disk."""
        # Simplified implementation - would need full file writing logic
        pass
    
    async def _persist_events(self, events: List[ResourceEvent]) -> None:
        """Persist events to disk."""
        # Simplified implementation - would need full file writing logic
        pass
    
    async def _cleanup_disk_files(self, cutoff_date: datetime) -> int:
        """Clean up old disk files."""
        # Simplified implementation
        return 0
    
    async def _get_disk_stats(self) -> Dict[str, Any]:
        """Get disk statistics."""
        # Simplified implementation
        return {'event_count': 0, 'total_size': 0}

