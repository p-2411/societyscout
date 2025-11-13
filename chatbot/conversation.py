"""
Conversation Flow Module
Main conversation logic and state management
"""

from chatbot.memory import ConversationMemory
from chatbot.rules import ChatbotRules
from chatbot.fallbacks import FallbackHandler

class ConversationManager:
    """Manages the conversation flow and state"""

    def __init__(self, event_database):
        self.memory = ConversationMemory()
        self.rules = ChatbotRules()
        self.fallbacks = FallbackHandler()
        self.event_db = event_database
        self.state = 'initial'  # initial, searching, awaiting_clarification

    def process_message(self, user_input):
        """
        Process user message and generate response

        Args:
            user_input: User's message

        Returns:
            str: Bot's response
        """
        # Store user message in history
        self.memory.add_to_history('user', user_input)

        # Detect intent
        intent = self.rules.detect_intent(user_input)

        # Route to appropriate handler
        if intent == 'greeting':
            response = self._handle_greeting()
        elif intent == 'cancel':
            response = self._handle_cancel()
        elif intent == 'reset':
            response = self._handle_reset()
        elif intent == 'find_event':
            response = self._handle_event_search(user_input)
        elif intent == 'get_details':
            response = self._handle_event_details(user_input)
        else:
            response = self._handle_unknown(user_input)

        # Store bot response in history
        self.memory.add_to_history('bot', response)

        return response

    def _handle_greeting(self):
        """Handle greeting intent"""
        self.state = 'initial'
        return ("Hi there! I can help you find events happening at the university. "
                "What are you looking for?")

    def _handle_cancel(self):
        """Handle cancel command"""
        last_filter = self.memory.remove_last_filter()
        response = self.fallbacks.handle_cancel_command(last_filter)

        if self.memory.get_filters():
            current_filters = self._format_current_filters()
            response += f"\n\nYour current filters are: {current_filters}"

        return response

    def _handle_reset(self):
        """Handle reset command"""
        self.memory.reset()
        self.state = 'initial'
        return self.fallbacks.handle_reset_command()

    def _handle_event_search(self, user_input):
        """
        Handle event search request

        Args:
            user_input: User's search query

        Returns:
            str: Search results or request for clarification
        """
        # Normalize input to extract filters
        filters = self.rules.normalize_input(user_input)

        # Add filters to memory
        for filter_type, value in filters.items():
            if value and filter_type != 'keywords':
                self.memory.add_filter(filter_type, value)
            elif filter_type == 'keywords' and value:
                for keyword in value:
                    self.memory.add_filter('keyword', keyword)

        # Check if search is specific enough
        if self.rules.is_specific_search(filters):
            # Perform search
            results = self._search_events()

            if results:
                self.state = 'searching'
                return self._format_search_results(results)
            else:
                # No results found - use fallback
                return self._handle_no_results()
        else:
            # Ask for specific missing information
            self.state = 'awaiting_clarification'
            return self.fallbacks.request_specific_filters(filters)

    def _handle_event_details(self, user_input):
        """Handle request for event details"""
        # This would be implemented to show details of a specific event
        return "Please specify which event you'd like to know more about."

    def _handle_unknown(self, user_input):
        """Handle unknown or unclear input"""
        # Check if it's out of scope
        if not any(keyword in user_input.lower() for keyword in ['event', 'workshop', 'meetup', 'activity', 'find', 'search']):
            return self.fallbacks.handle_out_of_scope()

        # Otherwise, extract any filters from the input and ask for missing information
        filters = self.rules.normalize_input(user_input)
        return self.fallbacks.request_specific_filters(filters)

    def _search_events(self):
        """
        Search events database based on current filters

        Returns:
            list: Matching events
        """
        filters = self.memory.get_filters()

        if not filters:
            return self.event_db.get_all_events()

        # Apply filters to search
        results = self.event_db.search_events(filters)

        return results

    def _handle_no_results(self):
        """Handle scenario when no events match the search"""
        filters = self.memory.get_filters()

        # Try removing last filter to find similar results
        if filters:
            last_filter = self.memory.remove_last_filter()
            similar_results = self._search_events()

            if similar_results:
                response = self.fallbacks.handle_no_results(filters, suggest_broader=True)
                response += f"\n\nHowever, here are some similar events:\n"
                response += self._format_search_results(similar_results)
                # Add the filter back
                self.memory.add_filter(last_filter['type'], last_filter['value'])
                return response

        return self.fallbacks.handle_no_results(filters)

    def _format_search_results(self, results):
        """
        Format search results for display

        Args:
            results: List of event dictionaries

        Returns:
            str: Formatted results
        """
        if not results:
            return "No events found."

        # Grounding message
        response = self.fallbacks.get_grounding_message({'count': len(results)})
        response += "\n\n"

        # Format each event
        for i, event in enumerate(results[:5], 1):  # Show max 5 events
            response += f"{i}. {event['title']}\n"
            response += f"   Type: {event['type']}\n"
            response += f"   Date: {event['date']}\n"
            response += f"   Location: {event['location']}\n"
            if 'organizer' in event:
                response += f"   Organizer: {event['organizer']}\n"
            response += "\n"

        if len(results) > 5:
            response += f"... and {len(results) - 5} more events.\n"

        response += "\nWould you like to know more about any of these events?"

        return response

    def _format_current_filters(self):
        """Format current filters for display"""
        filters = self.memory.get_filters()
        if not filters:
            return "none"

        filter_strs = [f"{f['type']}: {f['value']}" for f in filters]
        return ", ".join(filter_strs)
