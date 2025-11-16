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
    GREETING_WORDS = ['hi', 'hello', 'hey', 'greetings', 'good', 'morning', 'afternoon', 'evening']

    # Known topic keywords (frame-slot approach for topic extraction)
    TOPIC_KEYWORDS = [
        # Technology & Computing
        'coding', 'programming', 'tech', 'technology', 'computer', 'software', 'hardware',
        'python', 'java', 'javascript', 'web', 'app', 'mobile', 'ai', 'ml', 'data', 'cyber',
        'security', 'blockchain', 'game', 'gaming', 'vr', 'ar', 'cloud', 'database',
        # Design & Creative
        'design', 'graphic', 'ui', 'ux', 'art', 'creative', 'photography', 'video',
        'animation', 'film', 'music', 'theater', 'performance', 'drawing', 'painting',
        # Business & Professional
        'business', 'entrepreneurship', 'startup', 'marketing', 'finance', 'accounting',
        'consulting', 'leadership', 'management', 'career', 'professional', 'internship',
        'networking', 'resume', 'interview',
        # Academic & Science
        'research', 'science', 'engineering', 'math', 'physics', 'chemistry', 'biology',
        'medicine', 'health', 'psychology', 'law', 'history', 'literature', 'language',
        # Social & Cultural
        'culture', 'cultural', 'diversity', 'community', 'volunteer', 'charity', 'social',
        'environment', 'sustainability', 'activism', 'politics', 'debate', 'discussion',
        # Sports & Wellness
        'sport', 'sports', 'fitness', 'yoga', 'wellness', 'mental', 'mindfulness',
        'meditation', 'dance', 'running', 'soccer', 'basketball', 'volleyball',
        # Food & Drink
        'food', 'cooking', 'baking', 'coffee', 'wine', 'dining', 'culinary', 'dumplings',
        # Outdoor & Activities
        'outdoor', 'hiking', 'beach', 'picnic', 'nature', 'camping', 'adventure',
        'motorcycle', 'ride', 'scenic', 'walking', 'swimming',
        # Event-specific tags
        'party', 'celebration', 'awards', 'graduation', 'year-end', 'festive', 'holiday',
        'bbq', 'fundraiser', 'marathon', 'competition', 'tournament', 'championships',
        'collaboration', 'teamwork', 'networking',
        # Gaming & Entertainment
        'board games', 'tabletop', 'rpg', 'pokemon', 'nintendo', 'gaming',
        # Academic Support
        'student', 'study', 'academic', 'exam', 'tutorial', 'session', 'training',
        'revision', 'mock', 'prep', 'gamsat', 'finals',
        # Other relevant topics
        'hackathon', 'showcase', 'exhibition', 'conference', 'panel', 'seminar',
        'relaxation', 'stress', 'casual', 'free', 'online'
    ]
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
        'some', 'any', 'all', 'every', 'each', 'lot', 'lots', 'much', 'many', 'few',
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
        'in', 'on', 'at', 'by', 'with', 'from', 'of', 'to', 'as', 'for',
        # Pronouns
        'i', 'me', 'my', 'mine', 'you', 'your', 'yours',
        # Conjunctions
        'and', 'or', 'but', 'nor', 'yet',
        # Other common words that aren't topics
        'involve', 'involves', 'involving', 'include', 'includes', 'including',
        'contain', 'contains', 'containing', 'feature', 'features', 'featuring'
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
        Convert plural words and verb forms to base form

        Args:
            word: Word to singularize

        Returns:
            str: Base form of the word
        """
        if len(word) <= 2:
            return word

        # Handle -ing verb forms (partying -> party, networking -> network)
        if word.endswith('ing') and len(word) > 4:
            base = word[:-3]  # Remove 'ing'
            # Check if we need to add 'y' back (partying -> party)
            if len(base) > 0 and base[-1] not in 'aeiou':
                # Try with 'y' suffix
                base_with_y = base + 'y'
                # Return the version with 'y' for consistency
                if base_with_y in ChatbotRules.EVENT_TYPES:
                    return base_with_y
            return base

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

        # Frame-slot approach: Extract topic keywords that match known topics
        # Only keep words that are either:
        # 1. In our TOPIC_KEYWORDS list (known relevant topics)
        # 2. Longer than 4 characters and not in exclusion lists (potential domain-specific terms)
        potential_keywords = [w for w in filtered_words
                             if w not in ChatbotRules.EVENT_TYPES
                             and w not in ChatbotRules.ORGANIZERS
                             and w not in ChatbotRules.DATE_WORDS
                             and w not in ChatbotRules.SEARCH_WORDS
                             and w not in ChatbotRules.GREETING_WORDS
                             and not w.isdigit()]

        # Validate keywords using frame-slot approach
        filters['keywords'] = [w for w in potential_keywords
                              if w in ChatbotRules.TOPIC_KEYWORDS  # Known topic
                              or len(w) >= 5]  # Or longer word (likely specific topic)

        return filters

    @staticmethod
    def contains_greeting(user_input):
        """
        Check if user input contains a greeting

        Args:
            user_input: User input string

        Returns:
            bool: True if input contains a greeting
        """
        normalized = user_input.lower().strip()
        tokens = normalized.split()
        # Check for greeting words and common greeting phrases
        greeting_phrases = ['good morning', 'good afternoon', 'good evening']
        if any(phrase in normalized for phrase in greeting_phrases):
            return True
        return any(word in ChatbotRules.GREETING_WORDS for word in tokens)

    @staticmethod
    def detect_intent(user_input):
        """
        Detect user intent from input (excluding greetings)

        Args:
            user_input: User input string

        Returns:
            str: Intent type (find_event, get_details, cancel, reset, etc.)
        """
        normalized = user_input.lower().strip()
        tokens = normalized.split()
        singular_tokens = [ChatbotRules.singularize(token) for token in tokens]

        # Uncertainty/don't know intent
        uncertainty_phrases = [
            "i don't know", "i dont know", "idk", "not sure", "unsure",
            "don't know", "dont know", "no idea", "no clue", "dunno",
            "whatever", "anything", "surprise me"
        ]
        if any(phrase in normalized for phrase in uncertainty_phrases):
            return 'uncertainty'

        # Positive responses (for random selection)
        positive_phrases = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'yea', 'ya']
        if normalized in positive_phrases or normalized.startswith(tuple(p + ' ' for p in positive_phrases)):
            return 'positive_response'

        # Negative responses
        negative_phrases = ['no', 'nah', 'nope', 'not really', 'no thanks', 'no thank you']
        if normalized in negative_phrases or any(phrase in normalized for phrase in negative_phrases):
            return 'negative_response'

        # Language change intent
        if 'language' in normalized or '语言' in normalized or 'langue' in normalized:
            return 'change_language'

        # Help intent
        for word in tokens:
            if word in ChatbotRules.HELP_KEYWORDS:
                return 'help'

        if 'remember this' in normalized or normalized.startswith('remember '):
            return 'remember_filters'
        if 'use saved' in normalized or 'use saved filters' in normalized or 'load saved filters' in normalized:
            return 'use_saved_filters'
        if 'reset except' in normalized:
            return 'reset_except'

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

        if ChatbotRules._contains_filter_tokens(singular_tokens):
            return 'find_event'

        # Greeting detection (as fallback if no other intent detected)
        if ChatbotRules.contains_greeting(user_input):
            return 'greeting'

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
