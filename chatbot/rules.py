"""Chatbot Rules Module
Implements conversation flow rules and input normalization
"""

import re
import string

class ChatbotRules:
    """Handles rule-based conversation logic"""

    # Keywords for different filter types
    EVENT_TYPES = ['workshop', 'meetup', 'lecture', 'seminar', 'party', 'social', 'networking']
    ORGANIZERS = ['arc', 'library', 'club', 'clubs', 'founders', 'makerspace', 'unsw']
    HELP_KEYWORDS = ['help', 'assist', 'assistance', 'support', 'guidance', 'how', 'info']
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
        'found', 'results', 'result',
        # Question words
        'whats', 'what', 'where', 'when', 'which', 'who',
        # State verbs
        'are', 'is', 'there', 'available', 'happening', 'going', 'on', 'around',
        # Action verbs
        'got', 'get', 'give', 'tell', 'suggest',
        # Intent words
        'looking', 'interested', 'want', 'need', 'like', 'love', 'prefer',
        # Participation
        'attend', 'join', 'participate', 'go', 'come',
        # Casual expressions
        'im', 'tryna', 'trying', 'wanna', 'gonna', 'gotta',
        # Help/assistance
        'help', 'assist', 'suggestions', 'options', 'ideas',
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
    def singularize(word):
        """
        Convert plural words to singular form

        Args:
            word: Word to singularize

        Returns:
            str: Singular form of the word
        """
        if len(word) <= 2:
            return word

        # Handle common plural patterns
        if word.endswith('ies') and len(word) > 3:
            # parties -> party, studies -> study
            return word[:-3] + 'y'
        elif word.endswith('ves'):
            # lives -> life, knives -> knife
            return word[:-3] + 'fe'
        elif word.endswith('ses') and len(word) > 3:
            # classes -> class, passes -> pass
            return word[:-2]
        elif word.endswith('s') and not word.endswith('ss'):
            # workshops -> workshop, events -> event
            # but not: class, pass, etc.
            return word[:-1]

        return word

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

        # Remove filler words and singularize
        words = text.split()
        filtered_words = [ChatbotRules.singularize(w) for w in words if w not in ChatbotRules.FILLER_WORDS]

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
        elif 'day' in text or 'days' in text:
            for word in words:
                if (word.isdigit()):
                    filters['date'] = word + " days"

        # Extract simple location references
        location = ChatbotRules._extract_location(text)
        if location:
            filters['location'] = location

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
        normalized = user_input.lower().strip()
        tokens = normalized.split()

        # Greeting detection
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon']
        for word in tokens:
            if word in greetings:
                return 'greeting'

        # Help intent
        for word in tokens:
            if word in ChatbotRules.HELP_KEYWORDS:
                return 'help'

        # Cancel/undo commands
        if any(word in ['cancel', 'undo', 'back'] for word in tokens):
            return 'cancel'

        # Reset commands
        if any(word in ['reset', 'restart', 'clear'] for word in tokens) or 'start over' in normalized:
            return 'reset'

        # Event details (phrases come before generic search detection)
        if any(word in ['details', 'detail'] for word in tokens):
            return 'get_details'
        if any(phrase in normalized for phrase in ['tell me more', 'more info', 'more about']):
            return 'get_details'
        if 'about' in tokens and any(token.isdigit() or token.startswith('evt') for token in tokens):
            return 'get_details'

        more_phrases = ['more events', 'show more', 'see more', 'more results', 'more please']
        if any(phrase in normalized for phrase in more_phrases):
            return 'more_results'

        # Event search
        search_keywords = ChatbotRules.SEARCH_WORDS
        for word in tokens:
            if word in search_keywords:
                return 'find_event'

        if ChatbotRules._contains_filter_tokens(tokens):
            return 'find_event'

        return 'unknown'

    @staticmethod
    def _contains_filter_tokens(tokens):
        """Check if the user mentioned known filter keywords"""
        return any([
            any(token in ChatbotRules.EVENT_TYPES for token in tokens),
            any(token in ChatbotRules.ORGANIZERS for token in tokens),
            any(token in ChatbotRules.DATE_WORDS for token in tokens),
            any(token.isdigit() for token in tokens)
        ])

    @staticmethod
    def _extract_location(text):
        """Basic extraction for locations mentioned with 'in' or 'at'"""
        label_match = re.search(r'location\s*[:=]\s*([a-z0-9\s]+)', text)
        if label_match:
            return label_match.group(1).strip().split()[0]

        match = re.search(r'\b(?:in|at)\s+([a-z0-9]+(?:\s+[a-z0-9]+)?)', text)
        if match:
            return match.group(1).strip().split()[0]
        return None

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
