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
from chatbot.conversation import ConversationManager
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

    # Test location extraction
    filters = ChatbotRules.normalize_input("Any events at Kensington campus?")
    assert filters['location'] == 'kensington', "Should extract location keyword"

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

    # Test help
    assert ChatbotRules.detect_intent("help me") == 'help', "Should detect help"

    # Filter-only replies should still route to find_event
    assert ChatbotRules.detect_intent("Arc") == 'find_event', "Organizer-only inputs should trigger find_event"
    assert ChatbotRules.detect_intent("this week") == 'find_event', "Date-only inputs should trigger find_event"
    assert ChatbotRules.detect_intent("workshops") == 'find_event', "Plural event types should trigger find_event"

    print("✓ Intent detection tests passed")

def test_help_response():
    """Ensure help intent returns overview and filter summary"""
    print("Testing Help Response...")

    db = EventDatabase('data/events.json')
    convo = ConversationManager(db)

    convo.memory.add_filter('event_type', 'workshop')
    response = convo.process_message("help")

    assert 'help you discover' in response.lower(), "Help response should describe capabilities"
    assert 'current filters' in response.lower(), "Help response should mention filters"
    assert 'workshop' in response.lower(), "Existing filters should be listed"

    print("✓ Help response tests passed")

def test_event_details_response():
    """Ensure event details intent surfaces event information"""
    print("Testing Event Details Response...")

    db = EventDatabase('data/events.json')
    convo = ConversationManager(db)

    convo.process_message("show me workshops")
    response = convo.process_message("tell me more about event 1")

    assert 'workshop' in response.lower(), "Details should mention event type"
    assert 'location:' in response.lower(), "Details should include location"
    assert 'register:' in response.lower(), "Details should include registration link"

    print("✓ Event details tests passed")

def test_results_flow():
    """Ensure results appear continuously with paging support"""
    print("Testing Results Flow...")

    db = EventDatabase('data/events.json')
    convo = ConversationManager(db)

    response = convo.process_message("workshop")
    assert "workshop events" in response.lower(), "Should acknowledge event type"
    assert "here are events closest matching" in response.lower(), "Should include header"
    assert ("still need" in response.lower()) or ("you can still add" in response.lower()), "Should list remaining specs"

    response = convo.process_message("more events")
    total_listed = response.lower().count("type:")
    assert total_listed == len(convo.last_results), "Should list all events for current filters"
    assert "that's every event" in response.lower(), "Should confirm when listing is complete"

    convo.memory.add_filter('organizer', 'arc')
    convo.memory.add_filter('date', 'this_week')
    convo.memory.add_filter('location', 'kensington')
    convo.memory.add_filter('keyword', 'tech')
    response = convo.process_message("show events please")
    assert "filters set" in response.lower(), "Should restate filters"
    assert "here are events closest matching" in response.lower(), "Should keep header"
    assert "you can still add" not in response.lower(), "Should skip missing-spec line when complete"

    print("✓ Results flow tests passed")

def test_unknown_actionable_suggestions():
    """Unknown inputs should provide actionable suggestions"""
    print("Testing Unknown Intent Suggestions...")

    db = EventDatabase('data/events.json')
    convo = ConversationManager(db)

    response = convo.process_message("???")
    assert 'help you discover unsw society events' in response.lower(), "Should restate purpose"
    assert 'try prompts like' in response.lower(), "Should offer suggestion list"

    convo.process_message("I want a workshop")
    response = convo.process_message("maybe arc")
    assert 'filters set' in response.lower(), "Should treat detected filters as context"

    print("✓ Unknown suggestion tests passed")

def test_saved_filter_presets():
    """Ensure remember/use saved filters workflow functions"""
    print("Testing Saved Filter Presets...")

    db = EventDatabase('data/events.json')
    convo = ConversationManager(db)

    convo.process_message("workshops next week in kensington")
    msg = convo.process_message("remember this")
    assert 'saved your current filters' in msg.lower(), "Should confirm preset saved"

    convo.process_message("reset")
    response = convo.process_message("use saved filters")
    assert 'filters set' in response.lower(), "Should reapply saved filters"
    assert 'here are events closest matching' in response.lower(), "Should show results with saved filters"

    print("✓ Saved filter preset tests passed")

def test_reset_except():
    """Ensure reset except keeps only requested filter type"""
    print("Testing Reset Except...")

    db = EventDatabase('data/events.json')
    convo = ConversationManager(db)

    convo.process_message("Arc workshops next week in library")
    response = convo.process_message("reset except date")
    remaining_filters = convo.memory.get_filters()
    assert len(remaining_filters) == 1 and remaining_filters[0]['type'] == 'date', "Only date filter should remain"
    assert 'keeping your date filters' in response.lower(), "Should mention retained filter"
    assert 'here are events closest matching' in response.lower(), "Should rerun search"

    print("✓ Reset except tests passed")

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
    msg_lower = msg.lower()
    assert 'sorry' in msg_lower or 'not sure' in msg_lower or 'clarify' in msg_lower, "Should acknowledge misunderstanding"

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
        test_help_response()
        test_event_details_response()
        test_results_flow()
        test_saved_filter_presets()
        test_reset_except()
        test_unknown_actionable_suggestions()

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
