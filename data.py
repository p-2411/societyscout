"""
Event Database Module
Handles loading and querying the events database
"""

import json
from datetime import datetime, timedelta

class EventDatabase:
    """Manages the events database"""

    def __init__(self, data_file='data/events.json'):
        self.data_file = data_file
        self.events = []
        self.load_events()

    def load_events(self):
        """Load events from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.events = data.get('events', [])
        except FileNotFoundError:
            print(f"Warning: Events file '{self.data_file}' not found")
            self.events = []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{self.data_file}'")
            self.events = []

    def get_all_events(self):
        """Get all events"""
        return self.events.copy()

    def search_events(self, filters):
        """
        Search events based on filters

        Args:
            filters: List of filter dictionaries with 'type' and 'value'

        Returns:
            list: Matching events
        """
        results = self.events.copy()

        for filter_item in filters:
            filter_type = filter_item['type']
            filter_value = filter_item['value'].lower()

            if filter_type == 'event_type':
                results = [e for e in results if e['type'].lower() == filter_value]

            elif filter_type == 'organizer':
                results = [e for e in results if e['organizer'].lower() == filter_value]

            elif filter_type == 'date':
                results = self._filter_by_date(results, filter_value)

            elif filter_type == 'location':
                results = [e for e in results if filter_value in e['location'].lower()]

            elif filter_type == 'keyword':
                results = self._filter_by_keyword(results, filter_value)

        return results

    def _filter_by_date(self, events, date_value):
        """Filter events by date"""
        today = datetime.now().date()

        if date_value == 'today':
            target_date = today
        elif date_value == 'tomorrow':
            target_date = today + timedelta(days=1)
        elif date_value == 'this_week':
            # Events within the next 7 days
            end_date = today + timedelta(days=7)
            return [e for e in events
                    if today <= datetime.fromisoformat(e['date']).date() <= end_date]
        elif date_value == 'next_week':
            # Events 7-14 days from now
            start_date = today + timedelta(days=7)
            end_date = today + timedelta(days=14)
            return [e for e in events
                    if start_date <= datetime.fromisoformat(e['date']).date() <= end_date]
        else:
            return events

        # Filter for specific date
        return [e for e in events
                if datetime.fromisoformat(e['date']).date() == target_date]

    def _filter_by_keyword(self, events, keyword):
        """Filter events by keyword (searches title, description, and tags)"""
        return [e for e in events if (
            keyword in e['title'].lower() or
            keyword in e['description'].lower() or
            any(keyword in tag.lower() for tag in e.get('tags', []))
        )]

    def get_event_by_id(self, event_id):
        """Get a specific event by ID"""
        for event in self.events:
            if event['id'] == event_id:
                return event
        return None

    def get_events_by_organizer(self, organizer):
        """Get all events by a specific organizer"""
        return [e for e in self.events if e['organizer'].lower() == organizer.lower()]

    def get_events_by_type(self, event_type):
        """Get all events of a specific type"""
        return [e for e in self.events if e['type'].lower() == event_type.lower()]
