"""
Chatbot Rules Module
Implements conversation flow rules and input normalization
"""

import re
from datetime import datetime

class ChatbotRules:
    """Handles rule-based conversation logic"""

    # Keywords for different filter types
    EVENT_TYPES = ['workshop', 'meetup', 'lecture', 'seminar', 'party', 'social', 'networking']
    ORGANIZERS = ['arc', 'library', 'club', 'clubs', 'founders', 'makerspace', 'unsw']
    FILLER_WORDS = ['the', 'a', 'an', 'uh', 'um', 'like', 'just']

    @staticmethod
    def normalize_input(user_input):
        """
        Normalize user input by removing filler words and extracting key information

        Args:
            user_input: Raw user input string

        Returns:
            dict: Normalized data with extracted filters
        """
        # Convert to lowercase
        text = user_input.lower().strip()

        # Remove filler words
        words = text.split()
        filtered_words = [w for w in words if w not in ChatbotRules.FILLER_WORDS]

        # Extract filters
        filters = {
            'event_type': None,
            'date': None,
            'location': None,
            'organizer': None,
            'keywords': []
        }

        # Check for event types
        for word in filtered_words:
            if word in ChatbotRules.EVENT_TYPES:
                filters['event_type'] = word

        # Check for organizers
        for word in filtered_words:
            if word in ChatbotRules.ORGANIZERS:
                filters['organizer'] = word

        # Extract date keywords
        if 'today' in text:
            filters['date'] = 'today'
        elif 'tomorrow' in text:
            filters['date'] = 'tomorrow'
        elif 'week' in text:
            if 'next' in text:
                filters['date'] = 'next_week'
            elif 'this' in text:
                filters['date'] = 'this_week'

        # Store remaining keywords
        filters['keywords'] = [w for w in filtered_words
                               if w not in ChatbotRules.EVENT_TYPES
                               and w not in ChatbotRules.ORGANIZERS
                               and w not in ['today', 'tomorrow', 'week', 'next', 'this']]

        return filters

    @staticmethod
    def detect_intent(user_input):
        """
        Detect user intent from input

        Args:
            user_input: User input string

        Returns:
            str: Intent type (greeting, find_event, get_details, cancel, reset, etc.)
        """
        text = user_input.lower().strip()

        # Greeting detection
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon']
        if any(greeting in text for greeting in greetings):
            return 'greeting'

        # Cancel/undo commands
        if text in ['cancel', 'undo', 'back']:
            return 'cancel'

        # Reset commands
        if text in ['reset', 'restart', 'clear', 'start over']:
            return 'reset'

        # Event search
        search_keywords = ['find', 'search', 'looking for', 'show me', 'events', 'what']
        if any(keyword in text for keyword in search_keywords):
            return 'find_event'

        # Event details
        if any(word in text for word in ['details', 'more info', 'tell me more', 'about']):
            return 'get_details'

        return 'unknown'

    @staticmethod
    def is_specific_search(filters):
        """
        Check if user provided specific search criteria

        Args:
            filters: Normalized filters dict

        Returns:
            bool: True if search has specific criteria
        """
        return any([
            filters['event_type'],
            filters['date'],
            filters['location'],
            filters['organizer'],
            len(filters['keywords']) > 0
        ])
