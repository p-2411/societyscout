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
