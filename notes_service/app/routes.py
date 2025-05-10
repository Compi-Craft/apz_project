from fastapi import APIRouter, HTTPException, Response, Depends, Header
from fastapi.security import OAuth2PasswordBearer
from typing import List
import pika
import json
from app.get_services import MONGO, RABBIT_MQ
from app.models import NoteCreate, NoteUpdate, Event, NoteAggregate
from uuid import uuid4
from pymongo import MongoClient
from datetime import datetime
import jwt
from fastapi import status

replica_set = "rs0"


client = MongoClient(
    host=MONGO,
    replicaSet=replica_set,
    serverSelectionTimeoutMS=5000
)
db = client["notes_db"]
events_collection = db["events"]

router = APIRouter()

JWT_SECRET = "your_secret_key"

def get_user_from_token(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")  # Assuming 'sub' is used as user identifier in the JWT payload
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token does not contain user ID")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

def publish_event(event):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ[0]))
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

@router.post("/notes")
def create_note(note: NoteCreate, user_id: str = Depends(get_user_from_token)):
    note_id = str(uuid4())
    event = Event(
        aggregate_id=note_id,
        user_id=user_id,
        event_type="NoteCreated",
        timestamp=datetime.utcnow(),
        data={"title": note.title, "content": note.content}
    )
    publish_event(event.dict())
    return {"note_id": note_id, "message": "Note created."}

@router.put("/notes/{note_id}")
def update_note(note_id: str, update: NoteUpdate, user_id: str = Depends(get_user_from_token)):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")
    if events[0]['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this note")

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
def delete_note(note_id: str, user_id: str = Depends(get_user_from_token)):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")

    # Ensure the user is the owner of the note
    if events[0]['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this note")

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
def get_note(note_id: str, user_id: str = Depends(get_user_from_token)):
    events = get_events_for_aggregate(note_id)
    if not events:
        raise HTTPException(status_code=404, detail="Note not found")

    aggregate = NoteAggregate(note_id)
    aggregate.load_from_events(events)

    if aggregate.state.get("deleted"):
        raise HTTPException(status_code=410, detail="Note was deleted")

    if aggregate.state.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this note")

    return aggregate.state

@router.get("/users/{user_id}/notes")
def get_user_notes(user_id: str, current_user: str = Depends(get_user_from_token)):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="You are not authorized to access these notes")
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
