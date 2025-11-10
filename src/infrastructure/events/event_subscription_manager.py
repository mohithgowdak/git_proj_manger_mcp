"""Event subscription manager for managing event subscriptions."""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from ...domain.resource_types import ResourceType
from .event_store import ResourceEvent
from ...infrastructure.logger import get_logger


class TransportType(str, Enum):
    """Transport type."""
    SSE = "sse"
    WEBHOOK = "webhook"
    INTERNAL = "internal"


@dataclass
class EventFilter:
    """Event filter."""
    resource_type: Optional[ResourceType] = None
    event_type: Optional[str] = None
    resource_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None


@dataclass
class EventSubscription:
    """Event subscription."""
    id: str
    client_id: str
    filters: List[EventFilter]
    transport: TransportType
    endpoint: Optional[str] = None
    last_event_id: Optional[str] = None
    created_at: str = ""
    expires_at: Optional[str] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriptionStats:
    """Subscription statistics."""
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    subscriptions_by_transport: Dict[str, int] = field(default_factory=dict)
    subscriptions_by_resource_type: Dict[str, int] = field(default_factory=dict)


class EventSubscriptionManager:
    """Event subscription manager."""
    
    def __init__(self):
        """Initialize event subscription manager."""
        self._logger = get_logger(self.__class__.__name__)
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._client_subscriptions: Dict[str, Set[str]] = {}
        self._resource_type_index: Dict[ResourceType, Set[str]] = {}
        self._event_type_index: Dict[str, Set[str]] = {}
    
    def subscribe(self, subscription_data: Dict[str, Any]) -> str:
        """Create a new event subscription."""
        subscription_id = self._generate_subscription_id()
        
        subscription = EventSubscription(
            id=subscription_id,
            client_id=subscription_data['client_id'],
            filters=[EventFilter(**f) if isinstance(f, dict) else f for f in subscription_data.get('filters', [])],
            transport=TransportType(subscription_data.get('transport', 'internal')),
            endpoint=subscription_data.get('endpoint'),
            created_at=datetime.now().isoformat(),
            active=True,
            metadata=subscription_data.get('metadata', {})
        )
        
        # Store subscription
        self._subscriptions[subscription_id] = subscription
        
        # Index by client
        if subscription.client_id not in self._client_subscriptions:
            self._client_subscriptions[subscription.client_id] = set()
        self._client_subscriptions[subscription.client_id].add(subscription_id)
        
        # Index by resource types and event types in filters
        self._index_subscription(subscription_id, subscription)
        
        self._logger.info(f"Created subscription {subscription_id} for client {subscription.client_id}")
        
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return False
        
        # Remove from indices
        self._remove_from_indices(subscription_id, subscription)
        
        # Remove from client index
        if subscription.client_id in self._client_subscriptions:
            self._client_subscriptions[subscription.client_id].discard(subscription_id)
            if not self._client_subscriptions[subscription.client_id]:
                del self._client_subscriptions[subscription.client_id]
        
        # Remove subscription
        del self._subscriptions[subscription_id]
        
        self._logger.info(f"Removed subscription {subscription_id} for client {subscription.client_id}")
        
        return True
    
    def unsubscribe_client(self, client_id: str) -> int:
        """Unsubscribe all subscriptions for a client."""
        subscription_ids = self._client_subscriptions.get(client_id, set())
        if not subscription_ids:
            return 0
        
        removed_count = 0
        for subscription_id in list(subscription_ids):
            if self.unsubscribe(subscription_id):
                removed_count += 1
        
        self._logger.info(f"Removed {removed_count} subscriptions for client {client_id}")
        return removed_count
    
    def get_subscription(self, subscription_id: str) -> Optional[EventSubscription]:
        """Get subscription by ID."""
        return self._subscriptions.get(subscription_id)
    
    def get_client_subscriptions(self, client_id: str) -> List[EventSubscription]:
        """Get all subscriptions for a client."""
        subscription_ids = self._client_subscriptions.get(client_id, set())
        return [self._subscriptions[sid] for sid in subscription_ids if sid in self._subscriptions]
    
    def find_matching_subscriptions(self, event: ResourceEvent) -> List[EventSubscription]:
        """Find subscriptions that match an event."""
        matching_subscriptions: List[EventSubscription] = []
        
        # Get potential subscriptions from indices
        potential_ids: Set[str] = set()
        
        # Check resource type index
        if event.resource_type in self._resource_type_index:
            potential_ids.update(self._resource_type_index[event.resource_type])
        
        # Check event type index
        if event.type in self._event_type_index:
            potential_ids.update(self._event_type_index[event.type])
        
        # If no indices match, check all subscriptions
        if not potential_ids:
            potential_ids = set(self._subscriptions.keys())
        
        # Check each potential subscription
        for subscription_id in potential_ids:
            subscription = self._subscriptions.get(subscription_id)
            if not subscription or not subscription.active:
                continue
            
            # Check if event matches any filter
            if self._event_matches_filters(event, subscription.filters):
                matching_subscriptions.append(subscription)
        
        return matching_subscriptions
    
    def get_stats(self) -> SubscriptionStats:
        """Get subscription statistics."""
        stats = SubscriptionStats(
            total_subscriptions=len(self._subscriptions),
            active_subscriptions=sum(1 for s in self._subscriptions.values() if s.active),
            subscriptions_by_transport={},
            subscriptions_by_resource_type={}
        )
        
        # Count by transport
        for subscription in self._subscriptions.values():
            transport = subscription.transport.value
            stats.subscriptions_by_transport[transport] = stats.subscriptions_by_transport.get(transport, 0) + 1
        
        # Count by resource type
        for subscription in self._subscriptions.values():
            for filter_obj in subscription.filters:
                if filter_obj.resource_type:
                    rt = filter_obj.resource_type.value
                    stats.subscriptions_by_resource_type[rt] = stats.subscriptions_by_resource_type.get(rt, 0) + 1
        
        return stats
    
    def _generate_subscription_id(self) -> str:
        """Generate subscription ID."""
        return str(uuid.uuid4())
    
    def _index_subscription(self, subscription_id: str, subscription: EventSubscription) -> None:
        """Index subscription by resource types and event types."""
        for filter_obj in subscription.filters:
            if filter_obj.resource_type:
                if filter_obj.resource_type not in self._resource_type_index:
                    self._resource_type_index[filter_obj.resource_type] = set()
                self._resource_type_index[filter_obj.resource_type].add(subscription_id)
            
            if filter_obj.event_type:
                if filter_obj.event_type not in self._event_type_index:
                    self._event_type_index[filter_obj.event_type] = set()
                self._event_type_index[filter_obj.event_type].add(subscription_id)
    
    def _remove_from_indices(self, subscription_id: str, subscription: EventSubscription) -> None:
        """Remove subscription from indices."""
        for filter_obj in subscription.filters:
            if filter_obj.resource_type and filter_obj.resource_type in self._resource_type_index:
                self._resource_type_index[filter_obj.resource_type].discard(subscription_id)
                if not self._resource_type_index[filter_obj.resource_type]:
                    del self._resource_type_index[filter_obj.resource_type]
            
            if filter_obj.event_type and filter_obj.event_type in self._event_type_index:
                self._event_type_index[filter_obj.event_type].discard(subscription_id)
                if not self._event_type_index[filter_obj.event_type]:
                    del self._event_type_index[filter_obj.event_type]
    
    def _event_matches_filters(self, event: ResourceEvent, filters: List[EventFilter]) -> bool:
        """Check if event matches any filter."""
        if not filters:
            return True
        
        for filter_obj in filters:
            if self._event_matches_filter(event, filter_obj):
                return True
        
        return False
    
    def _event_matches_filter(self, event: ResourceEvent, filter_obj: EventFilter) -> bool:
        """Check if event matches a single filter."""
        if filter_obj.resource_type and event.resource_type != filter_obj.resource_type.value:
            return False
        
        if filter_obj.event_type and event.type != filter_obj.event_type:
            return False
        
        if filter_obj.resource_id and event.resource_id != filter_obj.resource_id:
            return False
        
        if filter_obj.source and event.source != filter_obj.source:
            return False
        
        # Tags matching would need to be implemented based on event metadata
        # if filter_obj.tags:
        #     event_tags = event.metadata.get('tags', [])
        #     if not any(tag in event_tags for tag in filter_obj.tags):
        #         return False
        
        return True




