"""
Event bus for BensBot trading system.

This module provides a simple publish-subscribe pattern implementation
allowing system components to communicate with each other.
"""

import logging
from typing import Callable, Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

class EventBus:
    """
    Event bus for system-wide event publishing and subscribing.
    
    Acts as a central message broker allowing components to communicate
    without direct dependencies.
    """
    
    def __init__(self):
        """Initialize the event bus with empty subscriber lists."""
        self._subscribers: Dict[str, Set[Callable]] = {}
        logger.info("EventBus initialized")
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        
        self._subscribers[event_type].add(callback)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
            
        Returns:
            True if successfully unsubscribed, False otherwise
        """
        if event_type not in self._subscribers:
            logger.warning(f"Cannot unsubscribe from non-existent event type: {event_type}")
            return False
        
        try:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from event: {event_type}")
            
            # Clean up empty sets
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
                
            return True
        except KeyError:
            logger.warning(f"Callback not found for event type: {event_type}")
            return False
    
    def publish(self, event_type: str, data: Optional[Any] = None) -> int:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event to publish
            data: Optional data to pass to subscribers
            
        Returns:
            Number of subscribers notified
        """
        if event_type not in self._subscribers:
            logger.debug(f"No subscribers for event type: {event_type}")
            return 0
        
        subscribers = self._subscribers[event_type]
        logger.debug(f"Publishing event {event_type} to {len(subscribers)} subscribers")
        
        count = 0
        for callback in subscribers:
            try:
                callback(event_type, data)
                count += 1
            except Exception as e:
                logger.error(f"Error in subscriber callback for {event_type}: {e}")
        
        return count
    
    def has_subscribers(self, event_type: str) -> bool:
        """
        Check if an event type has subscribers.
        
        Args:
            event_type: Event type to check
            
        Returns:
            True if event type has subscribers, False otherwise
        """
        return event_type in self._subscribers and len(self._subscribers[event_type]) > 0
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get number of subscribers for an event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of subscribers for event type
        """
        if event_type not in self._subscribers:
            return 0
        return len(self._subscribers[event_type]) 