"""
Memory Management Module
Handles conversation memory, storing user preferences and filter history
"""

class ConversationMemory:
    """Manages memory for the chatbot conversation"""

    def __init__(self):
        self.event_filters = []
        self.conversation_history = []
        self.last_added_filter = None

    def add_filter(self, filter_type, value):
        """
        Add a filter to memory

        Args:
            filter_type: Type of filter (event_type, date, location, organizer)
            value: The filter value
        """
        filter_item = {
            'type': filter_type,
            'value': value
        }
        self.event_filters.append(filter_item)
        self.last_added_filter = filter_item

    def remove_last_filter(self):
        """Remove the most recently added filter (for cancel functionality)"""
        if self.event_filters:
            removed = self.event_filters.pop()
            self.last_added_filter = self.event_filters[-1] if self.event_filters else None
            return removed
        return None

    def clear_filters(self):
        """Clear all event filters"""
        self.event_filters = []
        self.last_added_filter = None

    def get_filters(self):
        """Get all current filters"""
        return self.event_filters.copy()

    def add_to_history(self, speaker, message):
        """
        Add a message to conversation history

        Args:
            speaker: 'user' or 'bot'
            message: The message content
        """
        self.conversation_history.append({
            'speaker': speaker,
            'message': message
        })

    def reset(self):
        """Reset all memory"""
        self.event_filters = []
        self.conversation_history = []
        self.last_added_filter = None

    def set_filters(self, filters):
        """Replace filters with provided list (each item is a dict)."""
        self.event_filters = [f.copy() for f in filters]
        self.last_added_filter = self.event_filters[-1] if self.event_filters else None
