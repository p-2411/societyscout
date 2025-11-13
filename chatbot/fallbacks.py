"""
Fallback and Exception Handling Module
Handles various error scenarios and edge cases
"""

import random

class FallbackHandler:
    """Manages fallback responses for various scenarios"""

    # Template responses for different scenarios
    GROUNDING_TEMPLATES = [
        "Here are some events on {date}",
        "I found {count} events matching your criteria",
        "Showing {event_type} events",
        "Events organized by {organizer}",
    ]

    MISUNDERSTANDING_RESPONSES = [
        "Sorry, I didn't quite catch that. Could you rephrase?",
        "I'm not sure I understand. Can you provide more details?",
        "Could you clarify what you're looking for?",
    ]

    NO_RESULTS_RESPONSES = [
        "I couldn't find any events matching those exact criteria.",
        "No events found with those filters.",
        "Unfortunately, there are no events matching your search.",
    ]

    @staticmethod
    def get_grounding_message(context):
        """
        Get a grounding message to acknowledge progress

        Args:
            context: Dictionary with context information

        Returns:
            str: Grounding message
        """
        template = random.choice(FallbackHandler.GROUNDING_TEMPLATES)

        # Fill in template with context
        message = template
        for key, value in context.items():
            placeholder = '{' + key + '}'
            if placeholder in message:
                message = message.replace(placeholder, str(value))

        return message

    @staticmethod
    def handle_misunderstanding():
        """Handle when bot doesn't understand user input"""
        base_response = random.choice(FallbackHandler.MISUNDERSTANDING_RESPONSES)
        suggestions = "\n\nYou can search by:\n- Event type (workshop, meetup, lecture)\n- Date (today, tomorrow, next week)\n- Organizer (Arc, Library, clubs)\n- Topics or keywords"
        return base_response + suggestions

    @staticmethod
    def handle_no_results(filters, suggest_broader=True):
        """
        Handle when no events are found

        Args:
            filters: The filters that produced no results
            suggest_broader: Whether to suggest broadening search

        Returns:
            str: Response message
        """
        response = random.choice(FallbackHandler.NO_RESULTS_RESPONSES)

        if suggest_broader and filters:
            response += "\n\nTry broadening your search by removing some filters, or try different keywords."

        return response

    @staticmethod
    def handle_out_of_scope():
        """Handle out-of-scope queries"""
        return ("I'm specifically designed to help you find UNSW events. "
                "I can't answer that question, but I'd be happy to help you discover "
                "workshops, meetups, lectures, and other campus events!")

    @staticmethod
    def handle_actionable_unknown(current_filters):
        """Provide purpose reminder and actionable suggestions for unclear input"""
        purpose = ("I help you discover UNSW society events based on event type, date, "
                   "location, organizer, or topics.")

        suggestions = ("Try prompts like:\n"
                       "- 'workshops this week'\n"
                       "- 'Arc events tomorrow'\n"
                       "- 'help' for more examples\n"
                       "- 'more events' to see additional matches")

        if current_filters:
            filters_text = ", ".join(current_filters)
            context = f"So far we have: {filters_text}."
            return f"{purpose}\n{context}\n{suggestions}"

        return f"{purpose}\n{suggestions}"

    @staticmethod
    def handle_system_error(error_type="general"):
        """
        Handle system errors

        Args:
            error_type: Type of error encountered

        Returns:
            str: Error message
        """
        if error_type == "database":
            return "I'm having trouble accessing the events database right now. Please try again in a moment."
        elif error_type == "network":
            return "There seems to be a connectivity issue. Please check your connection and try again."
        else:
            return "I encountered an unexpected error. Please try again or rephrase your request."

    @staticmethod
    def handle_cancel_command(last_filter):
        """
        Handle cancel command

        Args:
            last_filter: The filter that was just removed

        Returns:
            str: Confirmation message
        """
        if last_filter:
            return f"Removed '{last_filter['value']}' from your filters."
        else:
            return "There's nothing to cancel."

    @staticmethod
    def handle_reset_command():
        """Handle reset command"""
        return "Conversation reset! How can I help you find events today?"

    @staticmethod
    def clarify_reset_intent():
        """Ask user to clarify reset intention"""
        return ("Would you like me to:\n"
                "1. Clear just your most recent filter\n"
                "2. Restart the entire conversation\n"
                "Please type '1' or '2'")

    @staticmethod
    def request_specific_filters(filters):
        """
        Generate a targeted prompt based on what filters are present vs. missing

        Args:
            filters: Dictionary of current filters

        Returns:
            str: Specific prompt asking for missing information
        """
        # Identify what we have
        has_items = []
        if filters.get('date'):
            has_items.append(f"events in {filters['date']}")
        if filters.get('event_type'):
            has_items.append(f"{filters['event_type']} events")
        if filters.get('organizer'):
            has_items.append(f"events by {filters['organizer']}")
        if filters.get('location'):
            has_items.append(f"events at {filters['location']}")
        if filters.get('keywords'):
            has_items.append(f"events about {', '.join(filters['keywords'])}")

        # Build acknowledgment
        if has_items:
            acknowledgment = f"I see you're looking for {' '.join(has_items)}. "
        else:
            acknowledgment = "I'd be happy to help you find events! "

        # Determine what to ask for (prioritize in order: event type, date, then other)
        missing_prompts = []

        if not filters.get('event_type'):
            missing_prompts.append({
                'question': 'What type of event are you interested in?',
                'examples': 'workshop, meetup, lecture, seminar, party, social, networking'
            })

        if not filters.get('date'):
            missing_prompts.append({
                'question': 'When would you like to attend?',
                'examples': 'today, tomorrow, this week, next week'
            })

        if not filters.get('organizer') and not filters.get('location'):
            missing_prompts.append({
                'question': 'Any preference for organizer or location?',
                'examples': 'Arc, Library, Clubs, Founders, Makerspace, or a specific location'
            })

        # If we have nothing specific to ask, use generic prompt
        if not missing_prompts:
            return acknowledgment + "Let me search for events matching your criteria."

        # Ask for the first missing piece
        prompt = missing_prompts[0]
        response = acknowledgment + prompt['question']
        response += f"\n\nFor example: {prompt['examples']}"

        return response
