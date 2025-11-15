"""
Society Scout - Main Entry Point
UNSW Event Discovery Chatbot
"""

import sys
import time
from data import EventDatabase
from chatbot.conversation import ConversationManager

def typing_effect(text):
    """
    Display text with typing animation effect.
    Allocates 3 seconds for every 150 characters.

    Args:
        text: The text to display
    """
    if not text:
        return

    # Calculate duration: 3 seconds per 150 characters
    duration = (len(text) / 150) * 3

    # Calculate delay per character to fit within duration
    delay_per_char = duration / len(text)

    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay_per_char)

        # Add extra pause after sentence-ending punctuation
        if char in '.?':
            time.sleep(0.3)

    print()  # New line at the end

def main():
    """Main function to run the chatbot"""
    print("=" * 60)
    print("        SOCIETY SCOUT - UNSW Event Discovery")
    print("=" * 60)
    print()

    # Initialize the event database
    event_db = EventDatabase('data/events.json')
    print(f"Loaded {len(event_db.get_all_events())} events")
    print()

    # Initialize the conversation manager
    conversation = ConversationManager(event_db)

    # Start conversation
    print("Chatbot: ", end="")
    typing_effect("Hi there! I can help you find events happening at the university.\n         What are you looking for?")
    print()
    print("(Type 'quit' or 'exit' to end the conversation)")
    print("-" * 60)
    print()

    # Conversation loop
    while True:
        # Get user input
        user_input = input("You: ").strip()

        # Check for exit
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print()
            print("Chatbot: ", end="")
            typing_effect("Thanks for using Society Scout! Have a great day!")
            break

        if not user_input:
            continue

        # Process message
        response = conversation.process_message(user_input)

        # Display response with typing effect
        print()
        print("Chatbot: ", end="")
        typing_effect(response)
        print()
        print("-" * 60)
        print()

if __name__ == "__main__":
    main()
