# Society Scout

A chatbot designed to help UNSW students discover and engage with university events, improving student wellbeing and campus connectivity.

## Project Overview

**Team:** Team Rocket
**Members:** Anning Bao, Anthony Pagano, Parham Sepasgozar, Soham Tilekar, Stacy Lin
**Course:** DESN1000
**Date:** 07/10/2025

## Problem Statement

UNSW students struggle to find relevant university activities due to a lack of centralized platform for events from different entities (Arc, Library, Clubs, UNSW Founders, Makerspace, etc.). This leads to:
- Poor student connection to the university
- Missed opportunities for social engagement
- Difficulty finding events matching personal interests

## Solution

Society Scout is a chatbot that centralizes all UNSW events in one place, allowing students to:
- Search for events by type, date, location, and organizer
- Get personalized event recommendations
- Discover events that match their interests and schedule

## Key Features

- **Centralized Event Discovery**: Find all UNSW events in one place
- **Smart Filtering**: Search by keywords, dates, topics, and locations
- **Conversational Interface**: Natural language interaction
- **Memory Management**: Remembers user preferences throughout conversation
- **Fallback Handling**: Graceful error handling and helpful suggestions

## Success Metrics

- **Task Success Rate**: Recommend at least 1 event within 3 bot messages
- **Fallback Rate**: Keep below 25%
- **User Satisfaction**: Measured via one-click survey
- **Session Duration**: Complete tasks within 5 logical user responses

## Technology Stack

- Python 3
- Event Database (JSON)

## Project Structure

```
societyscout/
├── README.md
├── data.py                 # Data handling and database queries
├── chatbot/
│   ├── __init__.py
│   ├── conversation.py    # Conversation flow logic
│   ├── rules.py           # Chatbot rules and normalization
│   ├── memory.py          # Memory management
│   └── fallbacks.py       # Fallback and exception handling
├── data/
│   ├── events.json        # Sample events database
│   └── schema.json        # Database schema
├── tests/
│   └── test_chatbot.py
└── docs/
    ├── design_proposal.pdf
    └── conversation_flows.md
```

## Getting Started

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Run the chatbot
python main.py
```

## Chatbot Design Principles

### System Design Rules
1. **No Interruptions**: User is not able to respond while chatbot is responding.
2. **Grounding**: Provide feedback every time progress is made
3. **Memory Management**: Store keywords from user requests and bot confirmations

### Conversation Flow Rules
- **R1. Greeting & Introduction**: Welcome users and explain capabilities
- **R2. Filtered Event Search**: Query database using specific keywords
- **R3. General Event Search**: Ask for clarification when criteria is vague

### Fallback Handling
- Clear/Restart/Reset commands
- Cancel command for undo functionality
- Misunderstanding handling
- No results found
- Out-of-scope input handling
- System error handling

## Research Insights

Based on surveys with 28 UNSW students:
- 70% were first-year students
- 54% are active members of university clubs
- 50% said events don't match their interests or schedule
- Students rated their society experience 7.5/10 on average
- Main concerns: studying (30%) and social circle (20%)

## Future Enhancements

1. **NLP/ML/AI Integration**: Move from rule-based to ML-based understanding
2. **Multi-Turn Contextual Memory**: Enhanced conversation context
3. **API Integrations**: Calendar sync, booking systems
4. **Personalization**: Recommendations based on user profile and history

## Contributing

This is a university course project. Team members follow the Gantt chart for task allocation and deadlines.
