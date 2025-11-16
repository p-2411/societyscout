"""
Society Scout - Main Entry Point
UNSW Event Discovery Chatbot
"""

import sys
import time
import select
from data import EventDatabase
from chatbot.conversation import ConversationManager

def typing_effect(text):
    """
    Display text with typing animation effect.
    Allocates 3 seconds for every 150 characters.
    Press Enter to skip the animation.

    Args:
        text: The text to display
    """
    if not text:
        return

    # Save terminal settings and set to raw mode to prevent visible typing
    old_settings = None
    try:
        if sys.platform != 'win32' and sys.stdin.isatty():
            import tty
            import termios
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
    except:
        pass

    try:
        # Calculate duration: 3 seconds per 150 characters
        duration = (len(text) / 150) * 3

        # Calculate delay per character to fit within duration
        delay_per_char = duration / len(text)

        for i, char in enumerate(text):
            sys.stdout.write(char)
            sys.stdout.flush()

            # Check if Enter was pressed (non-blocking)
            if sys.platform != 'win32':
                # Unix-like systems (macOS, Linux)
                if select.select([sys.stdin], [], [], 0)[0]:
                    # Read the character
                    ch = sys.stdin.read(1)
                    # Check if it's Enter (newline or carriage return)
                    if ch in ['\n', '\r']:
                        # Enter was pressed, print remaining text immediately
                        sys.stdout.write(text[i+1:])
                        sys.stdout.flush()
                        break
                    # Ignore other keys
            else:
                # Windows systems
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':  # Enter key
                        # Print remaining text immediately
                        sys.stdout.write(text[i+1:])
                        sys.stdout.flush()
                        # Consume any remaining characters in buffer
                        while msvcrt.kbhit():
                            msvcrt.getch()
                        break
                    # Ignore other keys

            time.sleep(delay_per_char)

            # Add extra pause after sentence-ending punctuation
            if char in '.?':
                time.sleep(0.3)

        print()  # New line at the end

    finally:
        # Restore terminal settings
        if old_settings is not None:
            try:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                # Flush any remaining input
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
            except:
                pass

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
    print("(Type 'language' to change language | Type 'quit' or 'exit' to end)")
    print("(Press Enter during responses to skip the typing animation)")
    print("-" * 60)
    print()

    # Conversation loop
    while True:
        # Get user input
        user_input = input("You: ").strip()

        if not user_input:
            continue

        # Translate to English for exit command detection
        user_input_english = conversation.translator.translate_to_english(user_input)

        # Check for exit (check both original and translated)
        exit_keywords = ['quit', 'exit', 'bye', 'goodbye', 'bye bye']
        if user_input.lower() in exit_keywords or user_input_english.lower() in exit_keywords:
            print()
            print("Chatbot: ", end="")
            # Translate goodbye message to user's language
            goodbye_message = conversation.translator.translate("Thanks for using Society Scout! Have a great day!")
            typing_effect(goodbye_message)
            break

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
