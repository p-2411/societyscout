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
        self.state = 'initial'  # initial, searching, awaiting_clarification, awaiting_random_response
        self.last_results = []
        self.results_pointer = 0
        self.last_removed_filters = []
        self.saved_filters = None
        self.awaiting_random_confirmation = False

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

        # Check for greeting
        has_greeting = self.rules.contains_greeting(user_input)

        # Detect intent
        intent = self.rules.detect_intent(user_input)

        # Route to appropriate handler
        if intent == 'greeting':
            response = self._handle_greeting()
            self.awaiting_random_confirmation = False
        elif intent == 'uncertainty':
            response = self._handle_uncertainty()
        elif intent == 'positive_response' and self.awaiting_random_confirmation:
            response = self._handle_random_selection()
        elif intent == 'negative_response' and self.awaiting_random_confirmation:
            response = self._handle_decline_random()
        elif intent == 'cancel':
            response = self._handle_cancel()
            self.awaiting_random_confirmation = False
        elif intent == 'reset':
            response = self._handle_reset()
            self.awaiting_random_confirmation = False
        elif intent == 'help':
            response = self._handle_help()
            self.awaiting_random_confirmation = False
        elif intent == 'remember_filters':
            response = self._handle_remember_filters()
            self.awaiting_random_confirmation = False
        elif intent == 'use_saved_filters':
            response = self._handle_use_saved_filters()
            self.awaiting_random_confirmation = False
        elif intent == 'reset_except':
            response = self._handle_reset_except(user_input)
            self.awaiting_random_confirmation = False
        elif intent == 'find_event':
            response = self._handle_event_search(user_input)
            self.awaiting_random_confirmation = False
        elif intent == 'more_results':
            response = self._handle_more_results()
            self.awaiting_random_confirmation = False
        elif intent == 'get_details':
            response = self._handle_event_details(user_input)
            self.awaiting_random_confirmation = False
        else:
            response = self._handle_unknown(user_input)
            self.awaiting_random_confirmation = False

        # If there's a greeting and another intent, prepend short greeting
        if has_greeting and intent != 'greeting':
            response = "Hi there! " + response

        # Store bot response in history
        self.memory.add_to_history('bot', response)

        return response

    def _handle_greeting(self):
        """Handle greeting intent"""
        self.state = 'initial'
        intro = "Hi there! I help you discover UNSW society events."
        suggestions = ("Try something like 'workshops this week', 'Arc events tomorrow', "
                       "'help' for more tips, or 'more events' if you want additional options.")
        prompt = "What are you looking for today?"
        return f"{intro}\n{suggestions}\n{prompt}"

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

    def _handle_remember_filters(self):
        filters = self.memory.get_filters()
        if not filters:
            return "You don't have any filters yet to remember. Describe an event first."
        self.saved_filters = [f.copy() for f in filters]
        return ("Saved your current filters. Say 'use saved filters' anytime to apply them again.")

    def _handle_use_saved_filters(self):
        if not self.saved_filters:
            return "I don't have any saved filters yet. After setting some filters, say 'remember this'."
        self.memory.set_filters(self.saved_filters)
        return self._respond_with_current_filters(self._collect_filter_map())

    def _handle_reset_except(self, user_input):
        keep_type = self._parse_except_filter(user_input)
        if not keep_type:
            self.memory.reset()
            self.last_results = []
            self.results_pointer = 0
            self.last_removed_filters = []
            return ("I reset all filters. Tell me what kind of event you're after and I'll start fresh.")

        kept_filters = [f for f in self.memory.get_filters() if f['type'] == keep_type]
        self.memory.set_filters(kept_filters)
        message = ("Keeping your " + keep_type.replace('_', ' ') +
                   " filters and clearing the rest.")
        response = self._respond_with_current_filters(self._collect_filter_map())
        return message + "\n\n" + response

    def _handle_help(self):
        """Provide overview of bot capabilities and current filters"""
        help_text = [
            "=== SOCIETY SCOUT HELP ===\n",
            "I help you discover UNSW society events. You can search by combining different criteria:\n",

            "SEARCH BY EVENT TYPE:",
            "  • workshops, meetups, seminars, lectures",
            "  • social events, parties, networking events",
            "  Example: 'show me workshops'\n",

            "SEARCH BY DATE/TIME:",
            "  • today, tomorrow, this week, next week",
            "  • specific days: Monday, Tuesday, etc.",
            "  Example: 'events tomorrow' or 'workshops this week'\n",

            "SEARCH BY ORGANIZER:",
            "  • Arc, Library, clubs, specific club names",
            "  Example: 'Arc events' or 'Library workshops'\n",

            "SEARCH BY LOCATION:",
            "  • campus buildings, general locations",
            "  Example: 'events in Kensington' or 'workshops at the Library'\n",

            "SEARCH BY TOPIC/KEYWORDS:",
            "  • Any relevant topics like 'coding', 'design', 'tech', etc.",
            "  Example: 'tech workshops' or 'coding events'\n",

            "COMBINE CRITERIA:",
            "  • 'workshops about coding this week'",
            "  • 'Arc social events tomorrow'",
            "  • 'networking events in Kensington'\n",

            "USEFUL COMMANDS:",
            "  • 'help' - Show this help message",
            "  • 'cancel' - Undo your last filter",
            "  • 'reset' - Clear all filters and start over",
            "  • 'reset except [type]' - Clear all filters except one (e.g., 'reset except date')",
            "  • 'remember this' - Save your current filters",
            "  • 'use saved filters' - Reapply your saved filters",
            "  • 'more events' - See additional search results",
            "  • 'tell me about event [number]' - Get details about a specific event",
            "  • 'I don't know' - Get suggestions or random events\n",

            "TIPS:",
            "  • You can search with just one criterion or combine multiple",
            "  • If no exact matches are found, I'll show close alternatives",
            "  • Say hi or greet me anytime - I'm friendly!\n"
        ]

        current_filters = self._format_current_filters()
        help_text.append(f"YOUR CURRENT FILTERS: {current_filters}")

        return "\n".join(help_text)

    def _handle_uncertainty(self):
        """Handle when user expresses uncertainty or doesn't know what they want"""
        self.awaiting_random_confirmation = True
        self.state = 'awaiting_random_response'

        suggestions = (
            "No worries! Here are some ideas:\n\n"
            "Event types: workshops, meetups, seminars, social events, networking\n"
            "Times: today, tomorrow, this week, next week\n"
            "Organizers: Arc, Library, various clubs\n\n"
            "Or I can pick 3 random events for you to browse. Would you like that?"
        )
        return suggestions

    def _handle_random_selection(self):
        """Provide 3 random events when user confirms they want random selection"""
        import random

        self.awaiting_random_confirmation = False
        self.state = 'searching'

        all_events = self.event_db.get_all_events()

        if not all_events:
            return "Sorry, I don't have any events in the database right now."

        # Select up to 3 random events
        num_to_select = min(3, len(all_events))
        random_events = random.sample(all_events, num_to_select)

        self.last_results = random_events
        self.results_pointer = len(random_events)

        header = f"Here {'is a random event' if num_to_select == 1 else f'are {num_to_select} random events'} you might enjoy:"
        return self._format_search_results(random_events, header)

    def _handle_decline_random(self):
        """Handle when user declines random selection"""
        self.awaiting_random_confirmation = False
        self.state = 'initial'

        return (
            "No problem! Feel free to describe what you're looking for—like "
            "'workshops this week' or 'Arc events tomorrow'—and I'll help you find it."
        )

    def _handle_event_search(self, user_input):
        """Handle event search request"""
        filter_map = self._ingest_filters(user_input=user_input)

        # Check if any meaningful filters were actually extracted (excluding just keywords)
        has_structured_filters = any([
            filter_map.get('event_type'),
            filter_map.get('date'),
            filter_map.get('location'),
            filter_map.get('organizer')
        ])

        # Check if input explicitly mentions events/activities
        user_lower = user_input.lower()
        mentions_events = any(word in user_lower for word in ['event', 'events', 'activity', 'activities'])

        # Only proceed with search if we have structured filters OR
        # (have keywords AND user explicitly mentioned events)
        if not has_structured_filters:
            if not (filter_map.get('keywords') and mentions_events):
                # No meaningful search criteria, treat as unknown
                return self._handle_unknown(user_input)

        return self._respond_with_current_filters(filter_map)

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

        # Build beautifully formatted event details
        details = []

        # Header with title
        details.append("╔" + "═" * 70 + "╗")
        details.append(f"║  {event['title'].upper()}")
        details.append("╠" + "═" * 70 + "╣")

        # Event type
        event_type = event.get('type', 'event').replace('_', ' ').title()
        details.append(f"║  📋 Type: {event_type}")

        # Date and time
        time_info = event.get('time', 'TBA')
        date_info = event.get('date', 'TBD')

        if date_info != 'TBD':
            time_display = f"{date_info}"
            if time_info != 'TBA':
                time_display += f" at {time_info}"
            details.append(f"║  📅 When: {time_display}")
        elif time_info != 'TBA':
            details.append(f"║  📅 Time: {time_info}")

        # Location
        if location_info := event.get('location', 'TBA'):
            if location_info != 'TBA':
                details.append(f"║  📍 Where: {location_info}")

        # Organizer
        if organizer := event.get('organizer'):
            details.append(f"║  👥 Host: {organizer}")

        # Club
        if club := event.get('club_name'):
            details.append(f"║  🏛️  Club: {club}")

        # Cost
        if cost := event.get('cost'):
            details.append(f"║  💰 Cost: {cost}")

        # Topics
        if tags := event.get('tags'):
            topics_text = ", ".join(tags)
            details.append(f"║  🏷️  Topics: {topics_text}")

        # Description section
        if description := event.get('description'):
            details.append("╠" + "═" * 70 + "╣")
            details.append("║  📝 DESCRIPTION:")
            details.append("║")
            # Wrap description text
            desc_lines = description.split('\n')
            for line in desc_lines:
                if len(line) <= 66:
                    details.append(f"║  {line}")
                else:
                    # Simple word wrapping
                    words = line.split()
                    current_line = "║  "
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 68:
                            current_line += word + " "
                        else:
                            details.append(current_line.rstrip())
                            current_line = "║  " + word + " "
                    if current_line.strip() != "║":
                        details.append(current_line.rstrip())

        # Registration link
        if link := event.get('registration_link'):
            details.append("╠" + "═" * 70 + "╣")
            details.append(f"║  🔗 Register: {link}")

        details.append("╚" + "═" * 70 + "╝")
        details.append("")
        details.append("💡 Would you like details for another event?")

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
            filter_map = self._ingest_filters(parsed_filters=filters)
            return self._respond_with_current_filters(filter_map)

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

    def _handle_no_results(self, filter_map, ack=None, missing_line=None, followup_line=None):
        """Handle scenario when no events match the search"""
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

                # Only show ONE prompt at a time
                more_prompt = self._more_results_prompt(len(similar_results), self.results_pointer)
                if missing_line:
                    pass  # Already have missing info prompt
                elif more_prompt:
                    parts.append(more_prompt)
                elif followup_line:
                    parts.append(followup_line)

                return "\n\n".join(parts)

        for item in reversed(removed):
            self.memory.add_filter(item['type'], item['value'])

        self.last_results = []
        self.last_removed_filters = []
        parts = [text for text in [ack, missing_line] if text]
        parts.append("I couldn't find any events matching those criteria, even after broadening the search.")

        # Only show ONE prompt at a time
        if not missing_line and followup_line:
            parts.append(followup_line)

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
            return "I couldn't find any events matching that."

        lines = []
        if header:
            lines.append(header)
            lines.append("")

        for i, event in enumerate(results[:5], 1):  # Show max 5 events
            # Add visual separator
            lines.append("┌" + "─" * 70 + "┐")

            # Event number and title
            event_title = event['title']
            lines.append(f"│ [{i}] {event_title.upper()}")

            # Event type
            event_type = event.get('type', 'event').replace('_', ' ').title()
            lines.append(f"│     Type: {event_type}")

            # Date information
            if 'date' in event:
                date_info = event['date']
                if 'time' in event and event['time'] != 'TBA':
                    date_info += f" at {event['time']}"
                lines.append(f"│     📅 When: {date_info}")

            # Location
            if 'location' in event:
                lines.append(f"│     📍 Where: {event['location']}")

            # Organizer
            if 'organizer' in event:
                lines.append(f"│     👥 Host: {event['organizer']}")

            lines.append("└" + "─" * 70 + "┘")
            lines.append("")

        if len(results) > 5:
            remaining = len(results) - 5
            lines.append(f"✨ Plus {remaining} more event{'s' if remaining != 1 else ''} available!")
            lines.append("")

        # Always let users know they can get more details
        lines.append("💡 Say 'tell me about event 1' (or any number) to learn more about a specific event.")
        lines.append("🔄 Continue refining your search, or say 'reset' to start fresh.")

        return "\n".join(lines)

    def _render_results_response(self, ack, missing_line, followup_line, header, results):
        visible = results[:3]
        self.results_pointer = min(3, len(results))
        response_parts = [part for part in [ack, missing_line,
                                            self._format_search_results(visible, header)] if part]

        # Only show ONE prompt at a time (priority order: missing info > more results > other actions)
        more_prompt = self._more_results_prompt(len(results), self.results_pointer)

        if missing_line:
            # If asking for missing info, don't add other prompts
            pass
        elif more_prompt:
            # If there are more results, show that prompt
            response_parts.append(more_prompt)
        elif followup_line:
            # Otherwise show the action prompt
            response_parts.append(followup_line)

        return "\n\n".join(response_parts)

    def _handle_more_results(self):
        """Serve additional events beyond the first page"""
        if not self.last_results:
            return ("I don't have earlier results to extend. Tell me what kind of event you're "
                    "after and I'll search again.")

        filter_map = self._collect_filter_map()
        header = self._build_results_header(filter_map, self.last_removed_filters)
        response = self._format_search_results(self.last_results, header)
        self.results_pointer = len(self.last_results)

        missing = self._missing_required_filters(filter_map)
        missing_line = self._build_missing_prompt(missing)
        followup_line = self._build_followup_prompt()

        parts = [response, "That's all the events I found!"]

        # Only show ONE prompt at a time
        if missing_line:
            parts.append(missing_line)
        elif followup_line:
            parts.append(followup_line)

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

    def _format_filter_summary(self, filter_map):
        """Format filters into a human-readable summary"""
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

        return ", ".join(parts) if parts else None

    def _format_filter_acknowledgment(self, filter_map):
        """Format an acknowledgment message for the current filters"""
        summary = self._format_filter_summary(filter_map)
        if summary:
            return f"Looking for {summary}."
        return ("I don't have any filters yet. Tell me what you're in the mood for—"
                "maybe 'workshops this week' or 'Arc events tomorrow'.")

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

    def _build_missing_prompt(self, _missing):
        """Return a prioritized prompt for the most useful missing filter"""
        # Disabled: Don't prompt users for missing fields
        return None

    def _build_followup_prompt(self):
        # Always show the action prompt (missing prompts are disabled)
        # Note: Details prompt and refine/reset prompt are now in _format_search_results
        return None

    @staticmethod
    def _humanize_value(value):
        return value.replace('_', ' ')

    @staticmethod
    def _more_results_prompt(total, shown):
        if total > shown:
            remaining = total - shown
            label = "event" if remaining == 1 else "events"
            return f"There {'is' if remaining == 1 else 'are'} {remaining} more {label}. Say 'more events' to see them all."
        return ""

    def _build_results_header(self, filter_map, removed_filters=None):
        filters_text = self._format_filter_summary(filter_map)
        if not filters_text:
            filters_text = "your request"

        header = f"Here are events matching {filters_text}:"
        if removed_filters:
            # Format removed filters naturally
            removed_parts = []
            for item in removed_filters:
                filter_type = item['type'].replace('_', ' ')
                removed_parts.append(f"{filter_type} '{item['value']}'")

            removed_text = " and ".join(removed_parts) if len(removed_parts) <= 2 else ", ".join(removed_parts[:-1]) + f", and {removed_parts[-1]}"
            header = f"I couldn't find exact matches, so here are events close to {filters_text} (I relaxed the {removed_text} filter):"
        return header

    def _parse_except_filter(self, user_input):
        text = user_input.lower()
        if 'except' not in text:
            return None

        mapping = [
            ('event type', 'event_type'),
            ('event', 'event_type'),
            ('type', 'event_type'),
            ('date', 'date'),
            ('time', 'date'),
            ('day', 'date'),
            ('location', 'location'),
            ('place', 'location'),
            ('organizer', 'organizer'),
            ('host', 'organizer'),
            ('keyword', 'keyword'),
            ('keywords', 'keyword'),
            ('topic', 'keyword'),
            ('topics', 'keyword')
        ]

        for phrase, filter_type in mapping:
            if phrase in text:
                return filter_type
        return None

    def _ingest_filters(self, user_input=None, parsed_filters=None):
        filters = parsed_filters or self.rules.normalize_input(user_input or "")
        for filter_type, value in filters.items():
            if value and filter_type != 'keywords':
                self.memory.add_filter(filter_type, value)
            elif filter_type == 'keywords' and value:
                for keyword in value:
                    self.memory.add_filter('keyword', keyword)
        return self._collect_filter_map()

    def _reset_paging(self, results, removed_filters=None):
        self.state = 'searching'
        self.last_results = results
        self.results_pointer = 0 if results else 0
        self.last_removed_filters = removed_filters or []

    def _respond_with_current_filters(self, filter_map=None):
        filter_map = filter_map or self._collect_filter_map()
        ack = self._format_filter_acknowledgment(filter_map)
        missing = self._missing_required_filters(filter_map)
        missing_line = self._build_missing_prompt(missing)
        followup_line = self._build_followup_prompt()

        results = self._search_events()
        self._reset_paging(results)

        if results:
            header = self._build_results_header(filter_map, self.last_removed_filters)
            return self._render_results_response(ack, missing_line, followup_line, header, results)

        return self._handle_no_results(filter_map, ack, missing_line, followup_line)
