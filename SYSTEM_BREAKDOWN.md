# Society Scout - System Architecture & Component Breakdown

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Key Features & Implementation](#key-features--implementation)
6. [Component Interactions](#component-interactions)

---

## System Overview

**Society Scout** is a rule-based conversational chatbot designed to help UNSW students discover university events through natural language interaction. The system follows a modular architecture with clear separation of concerns.

### Core Design Principles
- **Rule-Based NLP**: Uses pattern matching and keyword extraction instead of ML models
- **Stateful Conversation**: Maintains context and filters throughout the session
- **Graceful Degradation**: Handles errors and unclear inputs with helpful fallbacks
- **Multilingual Support**: Bidirectional translation for Chinese, French, and English

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                          │
│                           (main.py)                              │
│  • Terminal I/O with typing animation                            │
│  • Exit command handling                                         │
│  • Language detection for exit commands                          │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONVERSATION MANAGER                           │
│                  (chatbot/conversation.py)                       │
│  • Central orchestrator for all chatbot logic                    │
│  • Routes intents to appropriate handlers                        │
│  • Manages conversation state & flow                             │
└──┬────────┬──────────┬──────────┬──────────┬──────────┬─────────┘
   │        │          │          │          │          │
   ▼        ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌─────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│RULES │ │MEMO │ │FALLBACK │ │TRANSLTR│ │DATA DB │ │EVENT DB  │
│      │ │ RY  │ │         │ │        │ │        │ │          │
└──────┘ └─────┘ └─────────┘ └────────┘ └────────┘ └──────────┘
   │        │          │          │          │          │
   └────────┴──────────┴──────────┴──────────┴──────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  SEARCH RESULTS │
              │  & RESPONSES    │
              └─────────────────┘
```

---

## Component Details

### 1. **Main Entry Point** (`main.py`)

**Purpose**: User interface layer and application entry point

**Responsibilities**:
- Initialize event database and conversation manager
- Handle terminal I/O with typing animation effect
- Process exit commands (multilingual support)
- Display responses with skippable typing animation

**Key Functions**:
- `typing_effect(text)`: Displays text character-by-character with timing based on text length
- `main()`: Main conversation loop

**Data Flow**:
```
User Input → Translation Check → Exit Detection → ConversationManager.process_message()
                                                          ↓
                                                    Translated Response
                                                          ↓
                                                   Typing Animation
```

---

### 2. **Conversation Manager** (`chatbot/conversation.py`)

**Purpose**: Central orchestrator coordinating all chatbot components

**Responsibilities**:
- Intent routing and handler selection
- State management (initial, searching, awaiting_clarification)
- Filter ingestion and validation
- Search coordination with database
- Response formatting and grounding messages
- Pagination of search results

**Key State Variables**:
```python
self.state                      # Conversation state
self.last_results              # Cached search results
self.results_pointer           # Pagination tracker
self.last_removed_filters      # For relaxing search criteria
self.saved_filters            # User-saved filter presets
self.awaiting_random_confirmation  # Random event flow state
```

**Intent Handlers**:
| Intent | Handler | Description |
|--------|---------|-------------|
| `greeting` | `_handle_greeting()` | Welcome message and capabilities |
| `change_language` | `_handle_language_change()` | Switch UI language |
| `find_event` | `_handle_event_search()` | Main search functionality |
| `more_results` | `_handle_more_results()` | Show additional results |
| `get_details` | `_handle_event_details()` | Event detail view |
| `cancel` | `_handle_cancel()` | Undo last filter |
| `reset` | `_handle_reset()` | Clear all filters |
| `reset_except` | `_handle_reset_except()` | Selective filter clearing |
| `help` | `_handle_help()` | Show help documentation |
| `uncertainty` | `_handle_uncertainty()` | Handle "I don't know" |
| `remember_filters` | `_handle_remember_filters()` | Save current filters |
| `use_saved_filters` | `_handle_use_saved_filters()` | Restore saved filters |

**Search & Filter Flow**:
```
User Input → normalize_input() → Extract Filters → Add to Memory
                                                         ↓
                                              Search Database
                                                         ↓
                                      Results Found? ──No──> Relax Filters
                                            │
                                           Yes
                                            ↓
                                    Format & Display (max 3)
                                            ↓
                                    Store for pagination
```

---

### 3. **Rules Engine** (`chatbot/rules.py`)

**Purpose**: Natural language understanding through pattern matching

**Responsibilities**:
- Intent detection from user input
- Keyword extraction and normalization
- Word singularization (e.g., "workshops" → "workshop")
- Filter token detection

**Key Data Structures**:
```python
EVENT_TYPES = ['workshop', 'meetup', 'seminar', 'social']
ORGANIZERS = ['arc', 'library', 'club', 'clubs', 'founders', 'makerspace', 'unsw']
TOPIC_KEYWORDS = [keywords for known topics like 'tech', 'code', 'hike', etc.]
SEARCH_WORDS = [words indicating search intent like 'find', 'show', 'looking']
DATE_WORDS = ['today', 'tomorrow', 'week', 'monday', etc.]
FILLER_WORDS = ['the', 'a', 'like', 'just', etc.]
```

**Processing Pipeline**:
```
Raw Input: "I'm looking for hiking workshops tomorrow"
    ↓
Remove Punctuation: "im looking for hiking workshops tomorrow"
    ↓
Remove Filler Words: "looking hiking workshops tomorrow"
    ↓
Singularize: "look hike workshop tomorrow"
    ↓
Extract Filters:
  - event_type: "workshop"
  - keywords: ["hike"]
  - date: "tomorrow"
```

**Intent Detection Logic**:
1. Check for uncertainty phrases ("I don't know", "not sure")
2. Check for positive/negative responses (for confirmation flows)
3. Check for language change commands
4. Check for help keywords
5. Check for special commands (cancel, reset, remember, etc.)
6. Check for event details request
7. Check for "more results" phrases
8. Check for search keywords or filter tokens
9. Default to 'unknown'

**Singularization Algorithm**:
- Handles `-ing` forms: "hiking" → "hike"
- Handles plurals: "workshops" → "workshop"
- Handles special cases: "parties" → "party"

---

### 4. **Memory Manager** (`chatbot/memory.py`)

**Purpose**: Persistent state storage within a conversation session

**Data Stored**:
```python
event_filters = [
    {'type': 'event_type', 'value': 'workshop'},
    {'type': 'keyword', 'value': 'hike'},
    {'type': 'date', 'value': 'tomorrow'}
]

conversation_history = [
    {'speaker': 'user', 'message': 'looking for hiking workshops'},
    {'speaker': 'bot', 'message': 'Looking for workshop events...'}
]
```

**Operations**:
- `add_filter(type, value)`: Append new filter
- `remove_last_filter()`: Undo functionality
- `get_filters()`: Retrieve current filters
- `set_filters(filters)`: Replace all filters (for saved presets)
- `reset()`: Clear everything
- `add_to_history(speaker, message)`: Conversation logging

---

### 5. **Fallback Handler** (`chatbot/fallbacks.py`)

**Purpose**: Graceful error handling and helpful suggestions

**Fallback Scenarios**:
- **No Results Found**: Suggest broadening search
- **Misunderstanding**: Clarification prompt with examples
- **Out of Scope**: Redirect to chatbot capabilities
- **Actionable Unknown**: Provide specific suggestions
- **Cancel/Reset Confirmations**: User feedback
- **System Errors**: Database, network, or general errors

**Response Templates**:
```python
GROUNDING_TEMPLATES = [
    "Here are some events on {date}",
    "I found {count} events matching your criteria",
    ...
]

MISUNDERSTANDING_RESPONSES = [
    "Sorry, I didn't quite catch that...",
    ...
]
```

---

### 6. **Translation Service** (`chatbot/translator.py`)

**Purpose**: Multilingual support through bidirectional translation

**Supported Languages**:
- English (en)
- Chinese/Mandarin (zh-CN)
- French (fr)

**Translation Flow**:
```
User Types (Chinese): "我想找徒步活动"
         ↓
translate_to_english(): "I want to find hiking events"
         ↓
Process in English → Extract filters → Generate response
         ↓
translate(): "寻找徒步活动。"
         ↓
Display to User (Chinese)
```

**Key Methods**:
- `translate(text)`: English → Target Language (for bot responses)
- `translate_to_english(text)`: Target Language → English (for user input)
- `set_language(language)`: Change active language
- `get_language_menu()`: Display language options

**Implementation**:
- Uses Google Translate via `deep-translator` library
- Fallback to English if translation fails
- No translation if language is English

---

### 7. **Event Database** (`data.py`)

**Purpose**: Event data storage and querying

**Database Structure** (JSON):
```json
{
  "events": [
    {
      "event": {
        "id": "45929",
        "title": "Wandersoc Goes To: Mount Elliot Walk",
        "type": "other",
        "description": "...",
        "date": "2025-11-16",
        "time": "09:20:00",
        "location": "Central Station",
        "organizer": "club",
        "club_name": "WanderSoc",
        "tags": ["hike", "outdoor", "fitness"],
        "registration_link": "...",
        "capacity": null,
        "cost": "free"
      }
    }
  ]
}
```

**Query Operations**:
- `get_all_events()`: Return all events
- `search_events(filters)`: Filter by criteria
- `get_event_by_id(id)`: Retrieve specific event
- `get_events_by_organizer(organizer)`: Filter by host
- `get_events_by_type(type)`: Filter by category

**Filter Processing**:
```python
# Filters are applied sequentially
for filter_item in filters:
    if filter_type == 'event_type':
        results = [e for e in results if e['type'] == filter_value]
    elif filter_type == 'keyword':
        results = _filter_by_keyword(results, filter_value)
    elif filter_type == 'date':
        results = _filter_by_date(results, filter_value)
    # ... etc
```

**Keyword Matching**:
- Searches in: title, description, tags
- Case-insensitive substring matching
- Example: keyword "hike" matches tag "hike" or "hiking"

**Date Filtering**:
- Supports: today, tomorrow, this_week, next_week
- Calculates date ranges dynamically
- Uses ISO format dates

---

## Data Flow

### Complete Search Flow Example

**User Input**: "show me hiking workshops tomorrow"

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Input Reception (main.py)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> Check if exit command
                        │   └─> No
                        │
                        ├─> Translate to English (if needed)
                        │   └─> Already English
                        │
                        └─> Pass to ConversationManager
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 2: Conversation Processing (conversation.py)           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> Store in history
                        │
                        ├─> Detect intent (rules.py)
                        │   └─> Intent: 'find_event'
                        │
                        └─> Call _handle_event_search()
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 3: Filter Extraction (rules.py)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> normalize_input("show me hiking workshops tomorrow")
                        │   │
                        │   ├─> Remove punctuation
                        │   ├─> Remove filler words: ['show', 'me']
                        │   ├─> Remaining: ['hiking', 'workshops', 'tomorrow']
                        │   ├─> Singularize: ['hike', 'workshop', 'tomorrow']
                        │   │
                        │   └─> Extract filters:
                        │       {
                        │         'event_type': 'workshop',
                        │         'keywords': ['hike'],
                        │         'date': 'tomorrow',
                        │         'location': None,
                        │         'organizer': None
                        │       }
                        │
                        └─> Return to conversation.py
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 4: Filter Storage (memory.py)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> memory.add_filter('event_type', 'workshop')
                        ├─> memory.add_filter('keyword', 'hike')
                        └─> memory.add_filter('date', 'tomorrow')
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 5: Database Search (data.py)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> Get all events
                        │
                        ├─> Filter by event_type='workshop'
                        │   └─> 5 workshops found
                        │
                        ├─> Filter by keyword='hike' (in title/desc/tags)
                        │   └─> 1 workshop found
                        │
                        └─> Filter by date='tomorrow'
                            └─> 0 events found (none tomorrow)
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 6: Relaxation Logic (conversation.py)                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> No exact matches found
                        │
                        ├─> Remove last filter ('date')
                        │
                        ├─> Search again with remaining filters
                        │   └─> 1 event found!
                        │
                        └─> Store relaxed filter info
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 7: Response Formatting (conversation.py)               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> Build acknowledgment:
                        │   "Looking for workshop events, about hike, tomorrow."
                        │
                        ├─> Build results header:
                        │   "I couldn't find exact matches, so here are events
                        │    close to workshop events, about hike, tomorrow
                        │    (I relaxed the date 'tomorrow' filter):"
                        │
                        ├─> Format search results (max 3):
                        │   ┌──────────────────────────────────────┐
                        │   │ [1] HIKING WORKSHOP                   │
                        │   │     Type: Workshop                    │
                        │   │     📅 When: 2025-11-18 at 10:00:00  │
                        │   │     📍 Where: Campus                  │
                        │   │     🏷️  Tags: hike, outdoor, fitness │
                        │   └──────────────────────────────────────┘
                        │
                        └─> Add footer prompts
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 8: Translation (translator.py)                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> Check current language
                        │   └─> English (no translation needed)
                        │
                        └─> Return response
                                    │
┌───────────────────────────────────┴─────────────────────────┐
│ STEP 9: Display (main.py)                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─> Calculate typing speed
                        │   └─> ~3 seconds per 150 chars
                        │
                        ├─> Display with animation
                        │   └─> User can press Enter to skip
                        │
                        └─> Wait for next input
```

---

## Key Features & Implementation

### Feature 1: Filter Relaxation (Graceful Degradation)

**Problem**: User searches for "hiking workshop tomorrow" but no events match all criteria

**Solution**: Progressively remove filters until matches are found

```python
def _handle_no_results(self, filter_map):
    removed = []

    while self.memory.get_filters():
        # Remove most recent filter
        last_filter = self.memory.remove_last_filter()
        removed.append(last_filter)

        # Search with relaxed criteria
        results = self._search_events()

        if results:
            # Found matches! Inform user about relaxation
            header = f"I relaxed the {last_filter['type']} filter"
            return self._format_results(results, header)

    # No results even after relaxing everything
    return "No events found. Try different criteria."
```

**User Experience**:
```
User: "hiking workshops tomorrow"
Bot: "I couldn't find exact matches, so here are events close to
     your request (I relaxed the date 'tomorrow' filter):
     [Shows hiking workshops on other days]"
```

---

### Feature 2: Saved Filter Presets

**Purpose**: Let users save and reuse complex filter combinations

**Commands**:
- "remember this" → Save current filters
- "use saved filters" → Restore saved filters

**Implementation**:
```python
# Save
def _handle_remember_filters(self):
    filters = self.memory.get_filters()
    self.saved_filters = [f.copy() for f in filters]
    return "Saved your current filters."

# Restore
def _handle_use_saved_filters(self):
    self.memory.set_filters(self.saved_filters)
    return self._respond_with_current_filters()
```

**Use Case**:
```
User: "Arc workshops about tech this week"
Bot: [Shows results]
User: "remember this"
Bot: "Saved your current filters."
...later...
User: "use saved filters"
Bot: [Shows same Arc tech workshops this week]
```

---

### Feature 3: Selective Reset

**Purpose**: Clear specific filter types while keeping others

**Command**: "reset except [type]"

**Implementation**:
```python
def _handle_reset_except(self, user_input):
    keep_type = self._parse_except_filter(user_input)
    # e.g., "reset except date" → keep_type = 'date'

    kept_filters = [f for f in self.memory.get_filters()
                    if f['type'] == keep_type]

    self.memory.set_filters(kept_filters)
    return self._respond_with_current_filters()
```

**Use Case**:
```
User: "Arc workshops about tech tomorrow"
Bot: [Shows results]
User: "reset except date"
Bot: "Keeping your date filters and clearing the rest.
     Looking for events tomorrow."
```

---

### Feature 4: Multilingual Translation

**Flow**: User Input → English Processing → Translated Response

**Example (Chinese)**:
```
User types: "我想找徒步活动"
    ↓
TranslationService.translate_to_english()
    ↓ "I want to find hiking events"
    ↓
Rules.normalize_input()
    ↓ keywords: ['hike']
    ↓
Database search
    ↓ [hiking events found]
    ↓
Generate response: "Looking for hike events. Here are..."
    ↓
TranslationService.translate()
    ↓ "寻找徒步活动。以下是..."
    ↓
Display to user
```

---

### Feature 5: Context-Aware Grounding

**Purpose**: Acknowledge user progress with natural language feedback

**Examples**:

| User Input | Grounding Message |
|------------|-------------------|
| "workshops" | "Looking for workshop events." |
| "workshops about tech" | "Looking for workshop events, about tech." |
| "hike" | "Looking for hike events." |
| "Arc events tomorrow" | "Looking for events by Arc, tomorrow." |

**Implementation**:
```python
def _format_filter_summary(self, filter_map):
    parts = []

    if filter_map['event_type']:
        parts.append(f"{filter_map['event_type']} events")

    if filter_map['keywords']:
        if filter_map['event_type']:
            parts.append("about " + ", ".join(filter_map['keywords']))
        else:
            parts.append(f"{filter_map['keywords'][0]} events")

    if filter_map['organizer']:
        parts.append(f"by {filter_map['organizer']}")

    # ... etc

    return ", ".join(parts)
```

---

## Component Interactions

### Interaction Matrix

| Component | Interacts With | Purpose |
|-----------|---------------|---------|
| **main.py** | ConversationManager, TranslationService | UI layer, exit handling |
| **ConversationManager** | Rules, Memory, Fallbacks, Translator, EventDatabase | Central orchestration |
| **Rules** | *(standalone)* | Pure function transformations |
| **Memory** | *(standalone)* | State storage only |
| **Fallbacks** | *(standalone)* | Template responses |
| **Translator** | *(standalone via API)* | Translation service |
| **EventDatabase** | *(standalone)* | Data access layer |

### Call Sequence for Typical Search

```
main.py
  └─> ConversationManager.process_message(user_input)
       ├─> TranslationService.translate_to_english(user_input)
       ├─> Rules.contains_greeting(user_input)
       ├─> Rules.detect_intent(user_input)
       ├─> ConversationManager._handle_event_search(user_input)
       │    ├─> Rules.normalize_input(user_input)
       │    ├─> Memory.add_filter(type, value)  [multiple times]
       │    ├─> EventDatabase.search_events(filters)
       │    │    └─> EventDatabase._filter_by_keyword()
       │    │    └─> EventDatabase._filter_by_date()
       │    ├─> ConversationManager._format_search_results(results)
       │    └─> return formatted_response
       ├─> TranslationService.translate(response)
       └─> return translated_response
```

---

## State Management

### Conversation States

```python
self.state = 'initial'          # Start of conversation
           ↓
     'searching'                 # Actively searching for events
           ↓
     'awaiting_clarification'    # Needs more info from user
           ↓
     'awaiting_random_response'  # Waiting for yes/no to random events
```

### State Transitions

```
initial ─────[search query]────> searching
   │                                 │
   │                                 ├─[more results]──> searching
   │                                 │
   │                                 ├─[refine search]─> searching
   │                                 │
   │                                 └─[reset]─────────> initial
   │
   └─[I don't know]──> awaiting_random_response
                              │
                              ├─[yes]─────> searching (show random)
                              │
                              └─[no]──────> initial
```

---

## Error Handling Strategy

### 1. **No Results Found**
- **Strategy**: Progressive filter relaxation
- **User Experience**: "I relaxed the X filter to find matches"

### 2. **Ambiguous Input**
- **Strategy**: Ask for clarification with examples
- **User Experience**: "Try 'workshops this week' or 'Arc events'"

### 3. **Out of Scope**
- **Strategy**: Redirect to capabilities
- **User Experience**: "I help find UNSW events. Try asking about workshops..."

### 4. **Translation Failures**
- **Strategy**: Fallback to original language
- **User Experience**: Seamless (errors logged but not shown)

### 5. **Database Errors**
- **Strategy**: Generic error message
- **User Experience**: "Trouble accessing database. Please try again."

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Intent Detection | O(n) | n = number of patterns |
| Filter Extraction | O(m) | m = number of words in input |
| Event Search | O(e × f) | e = events, f = filters |
| Translation | O(1) | API call (network bound) |

### Space Complexity

| Component | Space | Notes |
|-----------|-------|-------|
| Event Database | O(e) | e = number of events |
| Conversation Memory | O(t) | t = conversation turns |
| Filter Storage | O(f) | f = number of active filters |

---

## Extension Points

### Adding New Intents

1. Add keyword patterns to `rules.py`
2. Add intent detection logic in `ChatbotRules.detect_intent()`
3. Create handler method in `ConversationManager`
4. Add routing in `process_message()`

### Adding New Languages

1. Add language code to `TranslationService.SUPPORTED_LANGUAGES`
2. Update `get_language_menu()` with new option
3. Add language-specific exit keywords in `main.py`
4. Update confirmation messages in `_handle_language_change()`

### Adding New Filter Types

1. Add filter type to `rules.py` constants
2. Update `normalize_input()` to extract new filter
3. Add database filtering logic in `data.py`
4. Update UI formatting in `conversation.py`

---

## Testing Strategy

### Unit Tests (`tests/test_chatbot.py`)

Tests should cover:
- Intent detection accuracy
- Filter extraction correctness
- Singularization logic
- Translation bidirectionality
- Database query results
- Memory state management

### Integration Tests

- End-to-end conversation flows
- Multi-turn contextual searches
- Filter relaxation scenarios
- Language switching mid-conversation

### Manual Testing Checklist

- [ ] Search with all filter types
- [ ] "more events" pagination
- [ ] "cancel" undo functionality
- [ ] "reset" clears everything
- [ ] "reset except [type]" selective clear
- [ ] Saved filter presets
- [ ] Language switching
- [ ] Multilingual exit commands
- [ ] Typing animation skipping
- [ ] No results → relaxation
- [ ] Random event flow
- [ ] Event details view

---

## Limitations & Future Work

### Current Limitations

1. **Rule-Based NLP**: Cannot handle complex linguistic variations
2. **No User Profiles**: Cannot personalize recommendations
3. **Static Database**: No real-time event updates
4. **Limited Context**: Cannot reference events from previous sessions
5. **No Fuzzy Matching**: Typos break keyword matching

### Planned Enhancements

1. **ML/NLP Integration**: Use transformers for intent detection
2. **User Authentication**: Track preferences across sessions
3. **API Integration**: Live data from Arc, Library, etc.
4. **Calendar Sync**: Add events to Google Calendar, iCal
5. **Recommendation Engine**: Suggest events based on history
6. **Spell Correction**: Handle typos gracefully
7. **Voice Interface**: Speech-to-text integration
8. **Mobile App**: Native iOS/Android apps

---

## Summary

Society Scout is a well-architected conversational system with clear separation of concerns:

- **main.py**: UI/UX layer
- **conversation.py**: Business logic orchestration
- **rules.py**: Natural language understanding
- **memory.py**: State persistence
- **fallbacks.py**: Error handling
- **translator.py**: Internationalization
- **data.py**: Data access layer

The modular design allows for easy extension and testing, while the rule-based approach provides deterministic, explainable behavior suitable for a university event discovery chatbot.
