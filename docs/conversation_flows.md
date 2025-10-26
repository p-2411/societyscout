# Society Scout - Conversation Flows

## Overview
This document describes the conversation flows implemented in Society Scout based on the design proposal.

## System Design Rules

### 1. No Interruptions
- Chat box is greyed out while bot is responding
- Users cannot send messages while processing

### 2. Grounding
Progress acknowledgment occurs when:
- Information is added to memory
- State is changed
- User request has been received successfully

Grounding messages use contextual templates:
- "Here are some events on {date}"
- "I found {count} events matching your criteria"
- "Showing {event_type} events"

### 3. Memory Management
- Stores keywords from both user requests and bot confirmations
- Tracks most recent addition for undo functionality
- Maintains conversation history

## Conversation Flow Rules

### R1: Greeting & Introduction

**Trigger:** User starts with greeting ("Hi", "Hello", "Hey")

**Action:** Bot responds with welcome message and prompts for more information

**Example:**
```
User: Hi
Bot: Hi there! I can help you find events happening at the university. What are you looking for?
```

**Fallback:** If user asks about events directly without greeting, this rule is skipped

---

### R2: Filtered Event Search

**Trigger:** User provides specific keywords (event type, date, topic)

**Action:**
1. Queries database using filters
2. Stores filters in memory
3. Returns matching results

**Example:**
```
User: Are there any marketing workshops next week?
Bot: [Searches for: type=workshop, topic=marketing, date=next week]
     I found 1 event matching your criteria

     1. Marketing Workshop: Digital Strategies
        Type: workshop
        Date: 2025-10-28
        Location: Quadrangle Building G055
        ...
```

**Fallback:** If no results found, provide similar results (by removing most recent filter) and suggest broadening search

---

### R3: General Event Search

**Trigger:** User hasn't specified keywords (date, topic, location)

**Action:** Ask for clarifying information

**Example:**
```
User: Show me events
Bot: Of course, I can search for events. Do you have anything specific in mind?
```

**Fallback:** Uses misunderstanding fallback to ask for specifics

---

## Normalization Process

Before processing, the system:

1. **Identifies primary goals:**
   - Find event: User wants to discover events
   - Get event details: User wants info about specific event

2. **Extracts relevant keywords:**
   - Event type (workshop, meetup, lecture, etc.)
   - Date (today, tomorrow, next week)
   - Location (building names)
   - Organizer (clubs, library, arc, etc.)

3. **Discards filler language:**
   - "the", "uh", "um", etc.

## Fallbacks & Exceptions

### 1. Clear/Restart/Reset Commands

**User input:** "clear", "restart", "reset"

**Action:**
1. Clarify intent: "Would you like me to just clear most recent filter, or restart the conversation?"
2. Based on response:
   - Clear most recent filter only, OR
   - Reset all memory

---

### 2. Cancel Command

**User input:** "cancel"

**Action:**
1. Delete most recent filter
2. Display success message
3. Show current remaining filters

**Example:**
```
User: cancel
Bot: Removed 'marketing' from your filters. Your current filters are: workshop, next week
```

---

### 3. Misunderstanding

**Occurs when:** User response doesn't match expected options

**Action:** Ask for clarification with examples

**Example:**
```
Bot: Sorry didn't catch that.

     You can search by:
     - Event type (workshop, meetup, lecture)
     - Date (today, tomorrow, next week)
     - Organizer (Arc, Library, clubs)
     - Topics or keywords
```

---

### 4. No Results Found

**Occurs when:** Valid query returns no events

**Action:**
1. Inform user clearly
2. Provide similar results (remove most recent filter)
3. Suggest broadening search

**Example:**
```
Bot: I couldn't find any events matching those exact criteria.

     However, here are some similar events:
     [Shows results without last filter]

     Try broadening your search by removing some filters.
```

---

### 5. Out-of-Scope Input

**Occurs when:** User asks unrelated questions

**Action:** Guide back to chatbot's purpose

**Example:**
```
User: What's the weather like?
Bot: I'm specifically designed to help you find UNSW events. I can't answer that
     question, but I'd be happy to help you discover workshops, meetups, lectures,
     and other campus events!
```

---

### 6. System Error

**Occurs when:** Technical issues arise

**Action:**
1. Inform user of specific error
2. Apologize for inconvenience
3. Suggest retry

**Types:**
- Database connection error
- Network error
- General unexpected error

---

## Success Metrics

### Task Success Rate
- **Target:** Recommend at least 1 event within 3 bot messages
- **Measurement:** Track conversations where user finds event without quitting

### Fallback Rate
- **Target:** Below 25%
- **Measurement:** Number of times fallback mechanisms are triggered

### User Satisfaction
- **Measurement:** One-click survey at end of conversation

### Session Duration
- **Target:** Complete within 5 logical user responses
- **Measurement:** Average time/response count per successful session

---

## Example Complete Conversation

```
Bot: Hi there! I can help you find events happening at the university.
     What are you looking for?

User: I want to find coding workshops

Bot: I found 1 event matching your criteria

     1. Python Coding Bootcamp
        Type: workshop
        Date: 2025-10-29
        Location: CSE Building K17 Seminar Room
        Organizer: UNSW Computing Society (CompSoc)

     Would you like to know more about any of these events?

User: Tell me more about the Python workshop

Bot: Python Coding Bootcamp

     Description: Beginner-friendly introduction to Python programming
     Time: 10:00
     Cost: Free for members, $5 non-members
     Capacity: 40 spots
     Registration: https://compsoc.org.au/events

     Can I help you find anything else?

User: No thanks

Bot: Thanks for using Society Scout! Have a great day!
```

---

## Future Enhancements

1. **NLP/ML Integration**
   - Understand complex phrasing
   - Synonym recognition
   - Context-aware responses

2. **Multi-turn Memory**
   - Remember context across multiple exchanges
   - Reference previous queries

3. **Personalization**
   - User profiles
   - Recommendation based on past attendance
   - Interest-based suggestions

4. **API Integrations**
   - Calendar sync
   - Ticket booking
   - Email reminders
