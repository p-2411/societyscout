"""
Chatbot Rules Module
Implements conversation flow rules and input normalization
"""

import string

class ChatbotRules:
    """Handles rule-based conversation logic"""

    # Keywords for different filter types
    EVENT_TYPES = ['workshop', 'meetup', 'lecture', 'seminar', 'party', 'social', 'networking']
    ORGANIZERS = ['arc', 'library', 'club', 'clubs', 'founders', 'makerspace', 'unsw']
    FILLER_WORDS = [
        # Articles
        'the', 'a', 'an',
        # Conversational fillers
        'uh', 'uhm', 'um', 'er', 'ah', 'oh', 'hmm',
        # Hedging words
        'like', 'just', 'so', 'well', 'basically', 'actually', 'literally',
        'seriously', 'really', 'very', 'pretty', 'kinda', 'sorta', 'kind', 'sort',
        # Uncertainty
        'maybe', 'probably', 'perhaps', 'possibly',
        # Quantifiers (general)
        'some', 'any', 'all', 'every', 'each',
        # Demonstratives
        'that', 'this', 'these', 'those', 'it', 'its',
        # Common verbs
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'done',
        # Modals
        'will', 'would', 'could', 'should', 'shall',
        'may', 'might', 'must', 'can', 'cant',
        # Prepositions
        'in', 'on', 'at', 'by', 'with', 'from', 'of', 'to', 'as',
        # Pronouns
        'i', 'me', 'my', 'mine', 'you', 'your', 'yours'
    ]

    SEARCH_WORDS = [
        # Direct search terms
        'find', 'search', 'locate', 'discover', 'browse', 'explore',
        # Display/view terms
        'show', 'see', 'check', 'list', 'view', 'display', 'pull', 'fetch',
        # Question words
        'whats', 'what', 'where', 'when', 'which', 'who',
        # State verbs
        'are', 'is', 'there', 'available', 'happening', 'going', 'on', 'around',
        # Action verbs
        'got', 'get', 'give', 'tell', 'suggest', 'recommend',
        # Intent words
        'looking', 'interested', 'want', 'need', 'like', 'love', 'prefer',
        # Participation
        'attend', 'join', 'participate', 'go', 'come',
        # Casual expressions
        'im', 'tryna', 'trying', 'wanna', 'gonna', 'gotta',
        # Help/assistance
        'help', 'assist', 'suggestions', 'recommendations', 'options', 'ideas',
        # Generic words
        'events', 'event', 'for', 'me', 'any', 'some', 'stuff', 'things',
        'upcoming', 'future', 'new',
        # Modals in search context
        'can', 'could', 'would', 'should'
    ]

    DATE_WORDS = [
        # Relative days
        'today', 'tomorrow', 'yesterday', 'tonight',
        # Day units
        'day', 'days',
        # Weeks
        'week', 'weeks', 'weekend', 'weekday', 'weekdays',
        # Months
        'month', 'months',
        # Years
        'year', 'years',
        # Temporal modifiers
        'next', 'this', 'last', 'coming', 'past', 'previous',
        'current', 'upcoming', 'future', 'recent',
        # Days of week
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
        # Times of day
        'morning', 'afternoon', 'evening', 'night', 'midday', 'noon', 'midnight',
        # Time indicators
        'now', 'soon', 'later', 'ago', 'before', 'after',
        # Months
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'jan', 'feb', 'mar', 'apr', 'may', 'jun',
        'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
    ]

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

        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))

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
            filters['date'] = '0 days'
        elif 'tomorrow' in text:
            filters['date'] = '1 days'
        elif 'week' in text:
            if 'next' in text:
                filters['date'] = '1 weeks'
            elif 'this' in text:
                filters['date'] = '0 weeks'
        elif 'day' or 'days' in text:
            for word in words:
                if (word.isdigit()):
                    filters['date'] = word + " days"

        # Store remaining keywords (exclude all common/filler words)
        filters['keywords'] = [w for w in filtered_words
                               if w not in ChatbotRules.EVENT_TYPES
                               and w not in ChatbotRules.ORGANIZERS
                               and w not in ChatbotRules.DATE_WORDS
                               and w not in ChatbotRules.SEARCH_WORDS
                               and not w.isdigit()]  # Also exclude numbers
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
        Requires at least event_type OR at least 2 other filters to be considered specific

        Args:
            filters: Normalized filters dict

        Returns:
            bool: True if search has specific criteria
        """
        # Count non-empty filters
        filter_count = sum([
            1 if filters['event_type'] else 0,
            1 if filters['date'] else 0,
            1 if filters['location'] else 0,
            1 if filters['organizer'] else 0,
            1 if len(filters['keywords']) > 0 else 0
        ])

        # Consider specific if:
        # 1. Has event_type (most important filter), OR
        # 2. Has at least 2 other filters (e.g., date + location, or date + organizer, etc.)
        return filters['event_type'] is not None or filter_count >= 2
