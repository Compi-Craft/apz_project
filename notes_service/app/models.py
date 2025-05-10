from pydantic import BaseModel
from datetime import datetime

class NoteCreate(BaseModel):
    user_id: str
    title: str
    content: str

class NoteUpdate(BaseModel):
    content: str

class Event(BaseModel):
    aggregate_id: str
    user_id: str
    event_type: str
    timestamp: datetime
    data: dict

class NoteAggregate:
    def __init__(self, note_id):
        self.note_id = note_id
        self.state = {}

    def apply_event(self, event):
        if event['event_type'] == 'NoteCreated':
            self.state = event['data']
            self.state['user_id'] = event['user_id']
        elif event['event_type'] == 'NoteUpdated':
            self.state['content'] = event['data']['content']
        elif event['event_type'] == 'NoteDeleted':
            self.state['deleted'] = True

    def load_from_events(self, events):
        for event in events:
            self.apply_event(event)