# Society Scout - Program Structure and Flow

## Project Overview

Society Scout is a conversational AI chatbot designed to help users discover UNSW society events through natural language search. It's built with pure Python using a rule-based architecture.

---

## Directory Structure

```
societyscout/
├── main.py                 # Entry point - main application loop
├── data.py                 # Event database manager
├── chatbot/                # Core chatbot logic
│   ├── conversation.py     # Orchestrates conversation flow
│   ├── rules.py           # Intent detection & input parsing
│   ├── memory.py          # Conversation state & filter tracking
│   └── fallbacks.py       # Error handling & response generation
├── data/                  # Data storage
│   ├── events.json        # 12 sample events
│   └── schema.json        # Event data schema
├── tests/
│   └── test_chatbot.py    # Unit tests
└── docs/
    └── conversation_flows.md
```

---

## Application Flow

### 1. Startup (main.py)

```
main.py:1-27
  ↓
Load events.json → Display welcome → Create ConversationManager → Input loop
```

**Key Steps:**
1. Initialize EventDatabase and load events from `data/events.json`
2. Display welcome banner with event count
3. Create ConversationManager instance
4. Enter main input loop

### 2. Message Processing (Core Loop)

```
User Input
  ↓
ConversationManager.process_message()
  ├─→ ChatbotRules.detect_intent()      # Identify what user wants
  │   Returns: 'greeting' | 'find_event' | 'help' | 'cancel' | 'reset' | 'get_details' | 'more_results' | 'unknown'
  ├─→ Route to appropriate handler
  │
  └─→ For 'find_event':
      ├─→ ChatbotRules.normalize_input()  # Extract filters from text (event type, date, location, organizer, keywords)
      ├─→ ConversationMemory.add_filter()  # Store new filters or keywords
      ├─→ ConversationManager acknowledges filters (“Filters set: ...”) and lists remaining specs
      ├─→ EventDatabase.search_events() → Always return best-effort matches
      │     ├─→ Results are shown immediately (first 3), header cites applied filters
      │     └─→ If more than 3, user can type “more events” to page through the rest
      └─→ If no exact matches → progressively remove filters, state which ones were dropped, and present closest alternatives
```

### 3. Complete Data Flow Diagram

```
User Input
    ↓
[main.py] Input Loop
    ↓
[conversation.py] process_message()
    ├→ [memory.py] add_to_history('user', input)
    ├→ [rules.py] detect_intent()
    │   └→ Returns: 'greeting' | 'find_event' | 'more_results' | 'cancel' | 'reset' | 'unknown'
    │
    ├→ [Routing to Intent Handler]
    │   └→ If 'find_event':
    │       ├→ [rules.py] normalize_input() → Extract filters
    │       ├→ [memory.py] add_filter() → Store filters
    │       ├→ [data.py] search_events(filters)
    │       ├→ [conversation.py] format first-page results + remaining-spec hints
    │       └→ [conversation.py] handles paging (“more events”) and closest-match fallbacks
    │
    └→ [memory.py] add_to_history('bot', response)
    ↓
[main.py] Display Response
    ↓
Loop Back to User Input
```

---

## Key Components

### ConversationManager (chatbot/conversation.py)

**Role:** Central orchestrator - coordinates all other components

**Key Methods:**
- `process_message(user_input)` - Main message processing pipeline
- `_handle_greeting()` - Handles greeting intents
- `_handle_cancel()` - Removes last filter
- `_handle_reset()` - Clears all memory
- `_handle_event_search(user_input)` - Orchestrates search workflow
- `_search_events()` - Executes database query
- `_format_search_results()` - Formats results for display

**State Management:**
- Maintains conversation state: `initial`, `searching`, `awaiting_clarification`
- Tracks `last_results`, `results_pointer`, and any `last_removed_filters` for paging/closest-match explanations
- Supports saved presets (`remember this`, `use saved filters`) and selective resets (`reset except <filter>`)
- Routes messages based on detected intent (`find_event`, `more_results`, `get_details`, etc.)

**Dependencies:**
- EventDatabase (passed in constructor)
- ConversationMemory (created internally)
- ChatbotRules (created internally)
- FallbackHandler (created internally)

### ChatbotRules (chatbot/rules.py)

**Role:** Natural language understanding engine

**Key Methods:**
- `detect_intent(user_input)` - Classifies user input into intent categories (find_event, help, more_results, get_details, etc.)
- `normalize_input(user_input)` - Extracts structured filters from natural language (event type, date, organizer, keywords, plus basic location parsing)

**Recognized Patterns:**

**Event Types:**
- workshop, meetup, lecture, seminar, party, social, networking

**Dates:**
- today, tomorrow, this_week, next_week

**Organizers:**
- arc, library, club, founders, makerspace, unsw

**Keywords:**
- Any remaining words after filtering out event types, dates, organizers, and filler words

**Processing Pipeline:**
1. Convert to lowercase and strip punctuation
2. Remove filler/search helper words, singularize plurals
3. Detect event types, organizers, relative dates (“today”, “this_week”, “next_week”, numeric “N days”)
4. Extract simple location hints (“in Kensington”, “location: Colombo”) with lightweight regex
5. Treat remaining meaningful tokens as keywords

**Recommendation Flow:**
- Every input triggers best-effort results: the bot summarizes current filters, lists missing specs, and shows the first 3 matching events (with a header quoting the filters).
- If more than 3 matches exist, the user can type “more events” to page through additional entries.
- When no exact matches exist, the bot progressively relaxes filters, explicitly naming the ones it removed before presenting the closest alternatives.

### ConversationMemory (chatbot/memory.py)

**Role:** Maintains conversation context and state

**Data Structures:**
- `event_filters` - List of active search criteria
- `conversation_history` - Full dialogue transcript
- `last_added_filter` - Reference for undo operations

**Key Methods:**
- `add_filter(filter_type, value)` - Stores user search criteria
- `remove_last_filter()` - Implements undo functionality
- `get_filters()` - Returns current active filters dictionary
- `add_to_history(speaker, message)` - Logs conversation
- `reset()` - Clears all memory

**Filter Structure:**
```python
{
    'event_type': ['workshop', 'meetup'],
    'date': ['tomorrow'],
    'location': ['Quad'],
    'organizer': ['arc'],
    'keywords': ['coding', 'python']
}
```

### EventDatabase (data.py)

**Role:** Data persistence and querying engine

**Key Methods:**
- `load_events()` - Loads JSON event database
- `get_all_events()` - Returns all events
- `search_events(filters)` - Performs multi-criteria search
- `get_events_by_type(event_type)` - Type-specific query
- `get_events_by_organizer(organizer)` - Organizer-specific query
- `_filter_by_date(events, date_filter)` - Date filtering with relative dates
- `_filter_by_keyword(events, keywords)` - Full-text search

**Event Schema:**
```json
{
    "id": "unique-identifier",
    "title": "Event Title",
    "type": "workshop|meetup|lecture|seminar|party|social|networking",
    "description": "Event description",
    "date": "YYYY-MM-DD or relative",
    "time": "HH:MM AM/PM",
    "location": "Venue name",
    "organizer": "Organization name",
    "club_name": "Club name (if applicable)",
    "tags": ["keyword1", "keyword2"],
    "registration_link": "URL",
    "capacity": "number",
    "cost": "Free or $amount"
}
```

**Search Capabilities:**
- Multi-criteria filtering (AND logic)
- Keyword search across title, description, and tags
- Relative date parsing (today, tomorrow, this week, next week)
- Case-insensitive matching

### FallbackHandler (chatbot/fallbacks.py)

**Role:** Graceful error handling and user guidance

**Key Methods:**
- `get_grounding_message(context)` - Acknowledges progress
- `handle_misunderstanding()` - Requests clarification
- `handle_no_results(filters, suggest_broader)` - Handles empty results
- `handle_out_of_scope()` - Redirects off-topic queries
- `handle_cancel_command(last_filter)` - Confirms filter removal
- `handle_reset_command()` - Confirms memory reset
- **`request_specific_filters(filters)` - NEW: Generates targeted prompts for missing information**

**Response Features:**
- Randomized templates for variety
- Context-aware dynamic content
- Helpful suggestions and examples
- **Context-aware targeted prompting** - acknowledges what user provided and asks specifically for missing filters

**Targeted Prompting Logic:**
When a user provides partial search criteria, the system:
1. Acknowledges what they've already specified
2. Asks specifically for the most important missing filter in priority order:
   - Event type (most important)
   - Date
   - Organizer/Location
3. Provides relevant examples for each filter type

---

## Module Dependency Graph

```
main.py (Entry Point)
  ├── data.py (EventDatabase)
  │   └── Uses: json, datetime
  └── chatbot/conversation.py (ConversationManager)
      ├── chatbot/memory.py (ConversationMemory)
      │   └── Uses: Python stdlib only
      ├── chatbot/rules.py (ChatbotRules)
      │   └── Uses: re (regex), datetime
      └── chatbot/fallbacks.py (FallbackHandler)
          └── Uses: random

tests/test_chatbot.py (Testing)
  ├── chatbot/memory.py
  ├── chatbot/rules.py
  ├── chatbot/fallbacks.py
  └── data.py
```

---

## Data Flow Example

### Example 1: Successful Search

**User Input:** "Find me a coding workshop tomorrow"

```
1. Input Processing
   └→ ConversationManager.process_message("Find me a coding workshop tomorrow")

2. Intent Detection
   └→ ChatbotRules.detect_intent()
   └→ Returns: 'find_event'

3. Filter Extraction
   └→ ChatbotRules.normalize_input()
   └→ Returns: {
        event_type: ['workshop'],
        date: ['tomorrow'],
        keywords: ['coding']
      }

4. Memory Storage
   └→ ConversationMemory.add_filter('event_type', 'workshop')
   └→ ConversationMemory.add_filter('date', 'tomorrow')
   └→ ConversationMemory.add_filter('keywords', 'coding')

5. Specificity Check
   └→ ChatbotRules.is_specific_search(filters)
   └→ Returns: True (has event type + additional criteria)

6. Database Search
   └→ EventDatabase.search_events({
        event_type: ['workshop'],
        date: ['tomorrow'],
        keywords: ['coding']
      })
   └→ Filters:
      - Events where type == 'workshop'
      - Events where date == tomorrow's date
      - Events where 'coding' in title/description/tags

7. Format Results
   └→ ConversationManager._format_search_results()
   └→ Output: "I found 1 event matching your criteria:

               Python Coding Bootcamp
               Oct 29, 2025 at 2:00 PM
               Location: Library Building Room 201
               ..."

8. Save to History
   └→ ConversationMemory.add_to_history('bot', response)

9. Display to User
   └→ main.py prints response
```

### Example 2: Partial Search Criteria - Targeted Prompting

**User Input:** "I'm tryna find events for the next 3 days"

```
1. Intent Detection → 'find_event'

2. Input Normalization
   └→ ChatbotRules.normalize_input()
   └→ Lowercase: "i'm tryna find events for the next 3 days"
   └→ Remove punctuation: "im tryna find events for the next 3 days"
   └→ Remove search words: ['im', 'tryna', 'find', 'events', 'for']
   └→ Extract date: '3 days'
   └→ Returns: {
        event_type: None,
        date: '3 days',
        location: None,
        organizer: None,
        keywords: []
      }

3. Specificity Check
   └→ is_specific_search(filters)
   └→ Returns: False (only 1 filter, no event type)

4. Request Specific Missing Information
   └→ FallbackHandler.request_specific_filters(filters)
   └→ Acknowledges: "I see you're looking for events in 3 days."
   └→ Asks specifically: "What type of event are you interested in?"
   └→ Provides examples: "workshop, meetup, lecture, seminar, party, social, networking"
```

### Example 3: Multiple Filters Without Event Type

**User Input:** "Find Arc events tomorrow"

```
1. Filter Extraction → {
     event_type: None,
     date: 'tomorrow',
     organizer: 'arc',
     keywords: []
   }

2. Specificity Check
   └→ is_specific_search(filters)
   └→ Returns: True (2 filters: date + organizer)

3. Database Search Executes
   └→ Searches for Arc events on tomorrow's date
   └→ Returns all matching events regardless of type
```

### Example 4: Cancel Last Filter

**User Input:** "cancel"

```
1. Intent Detection → 'cancel'

2. Remove Last Filter
   └→ ConversationMemory.remove_last_filter()
   └→ Removes most recent filter (e.g., 'keywords': 'coding')

3. Confirm to User
   └→ FallbackHandler.handle_cancel_command('keywords: coding')
   └→ "Removed the last filter (keywords: coding). Still searching with your other criteria."
```

---

## User Commands

### Search Commands
Natural language input is parsed for filters:
- "workshop about coding"
- "Arc events tomorrow"
- "networking events this week"
- "meetups at the Quad"

### Control Commands
- **cancel** - Removes the most recently added filter
- **reset** - Clears all memory and starts fresh
- **quit / exit / bye** - Exits the application

---

## Technology Stack

### Current Implementation
- **Language:** Pure Python 3.8+
- **Architecture:** Rule-based natural language processing
- **Data Format:** JSON-based event database
- **Testing:** unittest framework
- **Dependencies:** Python standard library only (no external packages required)

### Future Enhancements (from requirements.txt)
- **numpy** - For numerical computations in ML features
- **scikit-learn** - For ML-based intent detection
- **flask** - For web interface
- **pytest** - For advanced testing features

---

## Configuration Files

### requirements.txt
Defines Python package dependencies (currently all commented out for future use)

### data/schema.json
Documents the structure and validation rules for event objects

### data/events.json
Event database containing 12 sample events:
- Date range: Oct 28 - Nov 7, 2025
- Organizers: Arc, Library, Clubs, Founders, Makerspace, UNSW
- Various event types and topics

### .gitignore
Excludes build artifacts, virtual environments, IDE configs, and secrets from version control

---

## Testing Coverage

### test_chatbot.py includes tests for:

1. **Memory Management**
   - Filter addition, removal, and reset
   - Filter history tracking

2. **Input Normalization**
   - Event type extraction
   - Date extraction
   - Organizer extraction
   - Keyword preservation

3. **Intent Detection**
   - Greeting recognition
   - Search intent detection
   - Cancel/reset command recognition

4. **Database Operations**
   - Full database retrieval
   - Type-based filtering
   - Organizer-based filtering
   - Multi-filter combination

5. **Fallback Handling**
   - Grounding message generation
   - Misunderstanding responses
   - No results handling
   - Out-of-scope query handling

---

## Design Principles

1. **No Interruptions:** Chat box greyed out while bot responds
2. **Grounding:** Acknowledge progress with contextual messages
3. **Memory Management:** Store and track all filters for undo/cancel operations
4. **Graceful Degradation:** Fallback responses for edge cases
5. **Modularity:** Clear separation of concerns across components

---

## Success Metrics

- **Task Success Rate:** Recommend at least 1 event within 3 bot messages
- **Fallback Rate:** Keep below 25%
- **User Satisfaction:** Measured via one-click survey
- **Session Duration:** Complete tasks within 5 logical user responses

---

## Future Extensibility

The architecture supports future enhancements:

1. **Machine Learning Integration:**
   - Replace rule-based intent detection with ML models
   - Add sentiment analysis
  - Implement personalized suggestions

2. **Web Interface:**
   - Flask-based web app
   - REST API for event queries
   - Real-time chat interface

3. **Enhanced Data:**
   - Database integration (PostgreSQL/MongoDB)
   - Real-time event syncing
   - User preference storage

4. **Advanced Features:**
   - Multi-turn clarification dialogs
   - Event registration integration
   - Calendar export functionality
   - Push notifications for event reminders
