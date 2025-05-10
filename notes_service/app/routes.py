from fastapi import APIRouter, HTTPException, Response
from pymongo import MongoClient
from typing import List
import pika
import json
from app.get_services import MONGO
from app.models import NoteCreate, NoteUpdate, Event, NoteAggregate
from uuid import uuid4
from datetime import datetime

client = MongoClient(MONGO)
db = client["notes_db"]
events_collection = db["events"]

def publish_event(event):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='note_events', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='note_events',
        body=json.dumps(event, default=str),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

def get_events_for_aggregate(note_id: str) -> List[dict]:
    return list(events_collection.find({"aggregate_id": note_id}).sort("timestamp"))

def get_all_aggregates_for_user(user_id: str) -> List[str]:
    note_ids = events_collection.distinct("aggregate_id", {"user_id": user_id})
    return note_ids

router = APIRouter()

@router.post("/notes")
def create_note(note: NoteCreate):
    note_id = str(uuid4())
    event = Event(
        aggregate_id=note_id,
        user_id=note.user_id,
        event_type="NoteCreated",
        timestamp=datetime.utcnow(),
        data={"title": note.title, "content": note.content}
    )
    publish_event(event.dict())
    return {"note_id": note_id, "message": "Note created."}

@router.put("/notes/{note_id}")
def update_note(note_id: str, update: NoteUpdate):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")

    user_id = events[0]['user_id']

    event = Event(
        aggregate_id=note_id,
        user_id=user_id,
        event_type="NoteUpdated",
        timestamp=datetime.utcnow(),
        data={"content": update.content}
    )
    publish_event(event.dict())
    return {"message": "Note update requested."}

@router.delete("/notes/{note_id}")
def delete_note(note_id: str):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")

    user_id = events[0]['user_id']

    event = Event(
        aggregate_id=note_id,
        user_id=user_id,
        event_type="NoteDeleted",
        timestamp=datetime.utcnow(),
        data={}
    )
    publish_event(event.dict())
    return {"message": "Note delete requested."}

@router.get("/notes/{note_id}")
def get_note(note_id: str):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")

    aggregate = NoteAggregate(note_id)
    aggregate.load_from_events(events)

    if aggregate.state.get("deleted"):
        raise HTTPException(status_code=410, detail="Note was deleted")

    return aggregate.state

@router.get("/users/{user_id}/notes")
def get_user_notes(user_id: str):
    note_ids = get_all_aggregates_for_user(user_id)
    notes = []
    for note_id in note_ids:
        events = get_events_for_aggregate(note_id)
        if not events:
            continue
        aggregate = NoteAggregate(note_id)
        aggregate.load_from_events(events)
        if not aggregate.state.get("deleted"):
            notes.append({"note_id": note_id, **aggregate.state})
    return notes

@router.get("/notes/{note_id}/history")
def get_note_history(note_id: str):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")

    history = []
    for event in events:
        history.append({
            "event_type": event["event_type"],
            "timestamp": event["timestamp"],
            "data": event["data"]
        })
    return {"note_id": note_id, "history": history}

@router.get("/health")
def health_check(response: Response):
    response.status_code = 200
    return "OK"
