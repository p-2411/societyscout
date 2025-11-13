"""Conversation Flow Module
Main conversation logic and state management
"""

import re

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
        self.last_results = []
        self.results_pointer = 0
        self.last_removed_filters = []

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
        elif intent == 'help':
            response = self._handle_help()
        elif intent == 'find_event':
            response = self._handle_event_search(user_input)
        elif intent == 'more_results':
            response = self._handle_more_results()
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
        self.last_results = []
        self.results_pointer = 0
        self.last_removed_filters = []
        return self.fallbacks.handle_reset_command()

    def _handle_help(self):
        """Provide overview of bot capabilities and current filters"""
        overview = (
            "I help you discover UNSW society events. Describe what you're after using a mix of "
            "event types (workshops, meetups), dates (today, next week), organizers (Arc, clubs), "
            "locations, or topics (coding, design)."
        )

        guidance = (
            "You can say things like 'workshops this week', 'Arc events tomorrow', or "
            "'show me social events in Kensington'. Use 'cancel' to undo the last filter or "
            "'reset' to start fresh."
        )

        current_filters = self._format_current_filters()
        filters_msg = f"Current filters: {current_filters}"

        return f"{overview}\n\n{guidance}\n\n{filters_msg}"

    def _handle_event_search(self, user_input):
        """Handle event search request"""
        filters = self.rules.normalize_input(user_input)

        for filter_type, value in filters.items():
            if value and filter_type != 'keywords':
                self.memory.add_filter(filter_type, value)
            elif filter_type == 'keywords' and value:
                for keyword in value:
                    self.memory.add_filter('keyword', keyword)

        filter_map = self._collect_filter_map()
        ack = self._format_filter_acknowledgment(filter_map)
        missing = self._missing_required_filters(filter_map)
        missing_line = self._build_missing_prompt(missing)

        results = self._search_events()
        self.state = 'searching'
        self.last_results = results
        self.last_removed_filters = []
        self.results_pointer = 0

        if results:
            header = self._build_results_header(filter_map)
            return self._render_results_response(ack, missing_line, header, results)

        self.last_results = []
        return self._handle_no_results(filter_map, ack, missing_line)

    def _handle_event_details(self, user_input):
        """Handle request for event details"""
        user_text = user_input.lower()
        event = None

        # Try explicit event ID (e.g., evt003)
        match = re.search(r'(evt\d+)', user_text)
        if match:
            event_id = match.group(1).lower()
            event = self.event_db.get_event_by_id(event_id)

        # Try indexed reference from last search results (e.g., "event 2")
        if not event and self.last_results:
            number_match = re.search(r'\b(\d+)\b', user_text)
            if number_match:
                idx = int(number_match.group(1)) - 1
                if 0 <= idx < len(self.last_results):
                    event = self.last_results[idx]

        # Try matching by title fragment within last results
        if not event and self.last_results:
            for candidate in self.last_results:
                title = candidate['title'].lower()
                if title in user_text:
                    event = candidate
                    break

        # As a fallback, search entire database by title substring
        if not event:
            for candidate in self.event_db.get_all_events():
                if candidate['title'].lower() in user_text:
                    event = candidate
                    break

        if not event:
            if self.last_results:
                return ("I couldn't tell which event you meant. Please mention the event number "
                        "from the list or give me its event ID (like EVT003).")
            return ("I couldn't find that event. Try referencing the event number from the last "
                    "results or provide an event ID like EVT003.")

        details = [
            f"{event['title']} ({event['type'].title()})",
            f"Date: {event.get('date', 'TBD')} at {event.get('time', 'TBA')}",
            f"Location: {event.get('location', 'TBA')}"
        ]

        if organizer := event.get('organizer'):
            details.append(f"Organizer: {organizer}")

        if club := event.get('club_name'):
            details.append(f"Club: {club}")

        if description := event.get('description'):
            details.append("Description: " + description)

        if tags := event.get('tags'):
            details.append("Topics: " + ", ".join(tags))

        if link := event.get('registration_link'):
            details.append(f"Register: {link}")

        if cost := event.get('cost'):
            details.append(f"Cost: {cost}")

        details.append("Would you like details for another event?")

        return "\n".join(details)

    def _handle_unknown(self, user_input):
        """Handle unknown or unclear input"""
        user_lower = user_input.lower()
        tokens = user_lower.split()

        if not (ChatbotRules._contains_filter_tokens(tokens) or
                any(keyword in tokens for keyword in ['event', 'events', 'activity', 'activities', 'find', 'search'])):
            existing = self.memory.get_filters()
            current_filters = [f"{item['type']}={item['value']}" for item in existing]
            return self.fallbacks.handle_actionable_unknown(current_filters)

        filters = self.rules.normalize_input(user_input)

        # If we detected any new filters, add them and reuse the normal flow
        if any(value for key, value in filters.items() if key != 'keywords'):
            for filter_type, value in filters.items():
                if value and filter_type != 'keywords':
                    self.memory.add_filter(filter_type, value)
                elif filter_type == 'keywords' and value:
                    for keyword in value:
                        self.memory.add_filter('keyword', keyword)

            filter_map = self._collect_filter_map()
            ack = self._format_filter_acknowledgment(filter_map)
            missing = self._missing_required_filters(filter_map)
            missing_line = self._build_missing_prompt(missing)

            results = self._search_events()
            self.state = 'searching'
            self.last_results = results
            self.last_removed_filters = []
            self.results_pointer = 0

            if results:
                header = self._build_results_header(filter_map)
                return self._render_results_response(ack, missing_line, header, results)

            self.last_results = []
            return self._handle_no_results(filter_map, ack, missing_line)

        # Otherwise provide purpose reminder + actionable suggestions
        existing = self.memory.get_filters()
        current_filters = [f"{item['type']}={item['value']}" for item in existing]
        return self.fallbacks.handle_actionable_unknown(current_filters)

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

    def _handle_no_results(self, filter_map, ack=None, missing_line=None):
        """Handle scenario when no events match the search"""
        original_filters = self.memory.get_filters()
        removed = []

        while self.memory.get_filters():
            last_filter = self.memory.remove_last_filter()
            removed.append(last_filter)
            similar_results = self._search_events()

            if similar_results:
                header = self._build_results_header(filter_map, removed)
                visible = similar_results[:3]
                self.last_results = similar_results
                self.last_removed_filters = removed.copy()
                self.results_pointer = min(3, len(similar_results))

                for item in reversed(removed):
                    self.memory.add_filter(item['type'], item['value'])

                parts = [text for text in [ack, missing_line,
                                            self._format_search_results(visible, header)] if text]
                more_prompt = self._more_results_prompt(len(similar_results), self.results_pointer)
                if more_prompt:
                    parts.append(more_prompt)
                return "\n\n".join(parts)

        for item in reversed(removed):
            self.memory.add_filter(item['type'], item['value'])

        self.last_results = []
        self.last_removed_filters = []
        parts = [text for text in [ack, missing_line] if text]
        parts.append("No events available even after relaxing filters.")
        return "\n\n".join(parts)

    def _format_search_results(self, results, header=None):
        """
        Format search results for display

        Args:
            results: List of event dictionaries

        Returns:
            str: Formatted results
        """
        if not results:
            return "No events found."

        lines = []
        if header:
            lines.append(header)
            lines.append("")

        for i, event in enumerate(results[:5], 1):  # Show max 5 events
            lines.append(f"{i}. {event['title']}")
            lines.append(f"   Type: {event['type']}")
            lines.append(f"   Date: {event['date']}")
            lines.append(f"   Location: {event['location']}")
            if 'organizer' in event:
                lines.append(f"   Organizer: {event['organizer']}")
            lines.append("")

        if len(results) > 5:
            lines.append(f"... and {len(results) - 5} more events.")
            lines.append("")

        lines.append("Would you like to know more about any of these events?")

        return "\n".join(lines)

    def _render_results_response(self, ack, missing_line, header, results):
        visible = results[:3]
        self.results_pointer = min(3, len(results))
        response_parts = [part for part in [ack, missing_line,
                                            self._format_search_results(visible, header)] if part]
        more_prompt = self._more_results_prompt(len(results), self.results_pointer)
        if more_prompt:
            response_parts.append(more_prompt)
        return "\n\n".join(response_parts)

    def _handle_more_results(self):
        """Serve additional events beyond the first page"""
        if not self.last_results:
            return ("I don't have earlier results to extend. Tell me what kind of event you're "
                    "after and I'll search again.")

        if self.results_pointer >= len(self.last_results):
            return "You've seen all available events for the current filters."

        filter_map = self._collect_filter_map()
        header = self._build_results_header(filter_map, self.last_removed_filters)

        start = self.results_pointer
        end = min(start + 3, len(self.last_results))
        chunk = self.last_results[start:end]
        self.results_pointer = end

        response = self._format_search_results(chunk, header)
        more_prompt = self._more_results_prompt(len(self.last_results), self.results_pointer)
        missing_line = self._build_missing_prompt(self._missing_required_filters(filter_map))

        parts = [response]
        if more_prompt:
            parts.append(more_prompt)
        elif self.results_pointer >= len(self.last_results):
            parts.append("You've seen all available events for the current filters.")
        if missing_line:
            parts.append(missing_line)

        return "\n\n".join(parts)

    def _format_current_filters(self):
        """Format current filters for display"""
        filters = self.memory.get_filters()
        if not filters:
            return "none"

        filter_strs = [f"{f['type']}: {f['value']}" for f in filters]
        return ", ".join(filter_strs)

    def _collect_filter_map(self):
        filter_map = {
            'event_type': None,
            'date': None,
            'location': None,
            'organizer': None,
            'keywords': []
        }

        for item in self.memory.get_filters():
            ftype = item['type']
            if ftype == 'keyword':
                if item['value'] not in filter_map['keywords']:
                    filter_map['keywords'].append(item['value'])
            elif ftype in filter_map:
                filter_map[ftype] = item['value']

        return filter_map

    def _format_filter_acknowledgment(self, filter_map):
        parts = []
        if filter_map['event_type']:
            parts.append(f"{filter_map['event_type']} events")
        if filter_map['keywords']:
            parts.append("about " + ", ".join(filter_map['keywords']))
        if filter_map['organizer']:
            parts.append(f"by {filter_map['organizer']}")
        if filter_map['location']:
            parts.append(f"in {filter_map['location']}")
        if filter_map['date']:
            parts.append(self._humanize_value(filter_map['date']))

        if parts:
            return "Filters set: " + ", ".join(parts)
        return "No filters yet. Tell me what you're after."

    def _missing_required_filters(self, filter_map):
        missing = []
        if not filter_map['event_type']:
            missing.append('an event type')
        if not filter_map['date']:
            missing.append('a date/time')
        if not filter_map['location']:
            missing.append('a location')
        if not filter_map['organizer']:
            missing.append('an organizer')
        if not filter_map['keywords']:
            missing.append('some keywords/topics')
        return missing

    def _build_missing_prompt(self, missing):
        if not missing:
            return ""

        if len(missing) == 1:
            missing_text = missing[0]
        else:
            missing_text = ", ".join(missing[:-1]) + f", and {missing[-1]}"

        return f"You can still add {missing_text} for sharper matches."

    @staticmethod
    def _humanize_value(value):
        return value.replace('_', ' ')

    @staticmethod
    def _more_results_prompt(total, shown):
        if total > shown:
            remaining = total - shown
            label = "event" if remaining == 1 else "events"
            return f"{remaining} more {label} available. Say 'more events' to see them."
        return ""

    def _build_results_header(self, filter_map, removed_filters=None):
        filters_text = self._format_filter_acknowledgment(filter_map)
        filters_text = filters_text.replace("Filters set: ", "")
        if not filters_text or filters_text.startswith("No filters"):
            filters_text = "your request"

        header = f"Here are events closest matching {filters_text}."
        if removed_filters:
            removed_text = ", ".join(
                f"{item['type']}='{item['value']}'" for item in removed_filters)
            header += f" Removed {removed_text}."
        return header
