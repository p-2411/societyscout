"""
Society Scout - Main Entry Point
UNSW Event Discovery Chatbot
"""

from data import EventDatabase
from chatbot.conversation import ConversationManager

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
    print("Chatbot: Hi there! I can help you find events happening at the university.")
    print("         What are you looking for?")
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
            print("Chatbot: Thanks for using Society Scout! Have a great day!")
            break

        if not user_input:
            continue

        # Process message
        response = conversation.process_message(user_input)

        # Display response
        print()
        print(f"Chatbot: {response}")
        print()
        print("-" * 60)
        print()

if __name__ == "__main__":
    main()
