"""
Unit Tests for Society Scout Chatbot
Tests conversation logic, memory, and database functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot.memory import ConversationMemory
from chatbot.rules import ChatbotRules
from chatbot.fallbacks import FallbackHandler
from data import EventDatabase

def test_memory_management():
    """Test memory add, remove, and reset functionality"""
    print("Testing Memory Management...")
    memory = ConversationMemory()

    # Test adding filters
    memory.add_filter('event_type', 'workshop')
    memory.add_filter('date', 'tomorrow')

    filters = memory.get_filters()
    assert len(filters) == 2, "Should have 2 filters"
    assert filters[0]['value'] == 'workshop', "First filter should be 'workshop'"

    # Test removing last filter
    removed = memory.remove_last_filter()
    assert removed['value'] == 'tomorrow', "Should remove 'tomorrow'"
    assert len(memory.get_filters()) == 1, "Should have 1 filter remaining"

    # Test reset
    memory.reset()
    assert len(memory.get_filters()) == 0, "Should have no filters after reset"

    print("✓ Memory management tests passed")

def test_input_normalization():
    """Test input normalization and keyword extraction"""
    print("Testing Input Normalization...")

    # Test event type extraction
    filters = ChatbotRules.normalize_input("Find me a workshop about coding")
    assert filters['event_type'] == 'workshop', "Should extract 'workshop'"
    assert 'coding' in filters['keywords'], "Should extract 'coding' keyword"

    # Test date extraction
    filters = ChatbotRules.normalize_input("Show me events tomorrow")
    assert filters['date'] == 'tomorrow', "Should extract 'tomorrow'"

    # Test organizer extraction
    filters = ChatbotRules.normalize_input("What events does Arc have?")
    assert filters['organizer'] == 'arc', "Should extract 'arc'"

    print("✓ Input normalization tests passed")

def test_intent_detection():
    """Test intent detection from user input"""
    print("Testing Intent Detection...")

    # Test greeting
    assert ChatbotRules.detect_intent("Hello") == 'greeting', "Should detect greeting"

    # Test find event
    assert ChatbotRules.detect_intent("Find me events") == 'find_event', "Should detect find_event"

    # Test cancel
    assert ChatbotRules.detect_intent("cancel") == 'cancel', "Should detect cancel"

    # Test reset
    assert ChatbotRules.detect_intent("reset") == 'reset', "Should detect reset"

    print("✓ Intent detection tests passed")

def test_database_search():
    """Test database search functionality"""
    print("Testing Database Search...")

    db = EventDatabase('data/events.json')

    # Test get all events
    all_events = db.get_all_events()
    assert len(all_events) > 0, "Should have events in database"

    # Test search by type
    workshops = db.get_events_by_type('workshop')
    assert all(e['type'] == 'workshop' for e in workshops), "All should be workshops"

    # Test search by organizer
    arc_events = db.get_events_by_organizer('arc')
    assert all(e['organizer'] == 'arc' for e in arc_events), "All should be Arc events"

    # Test filtered search
    filters = [
        {'type': 'event_type', 'value': 'workshop'}
    ]
    results = db.search_events(filters)
    assert all(e['type'] == 'workshop' for e in results), "Filtered results should match"

    print("✓ Database search tests passed")

def test_fallback_messages():
    """Test fallback message generation"""
    print("Testing Fallback Messages...")

    handler = FallbackHandler()

    # Test grounding message
    msg = handler.get_grounding_message({'count': 5, 'date': 'tomorrow'})
    assert len(msg) > 0, "Should generate grounding message"

    # Test misunderstanding
    msg = handler.handle_misunderstanding()
    assert 'sorry' in msg.lower() or 'not sure' in msg.lower(), "Should apologize"

    # Test no results
    msg = handler.handle_no_results([])
    assert len(msg) > 0, "Should generate no results message"

    # Test out of scope
    msg = handler.handle_out_of_scope()
    assert 'events' in msg.lower(), "Should mention events"

    print("✓ Fallback message tests passed")

def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("Running Society Scout Chatbot Tests")
    print("=" * 60)
    print()

    try:
        test_memory_management()
        test_input_normalization()
        test_intent_detection()
        test_database_search()
        test_fallback_messages()

        print()
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"Test failed: {e}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    run_all_tests()
