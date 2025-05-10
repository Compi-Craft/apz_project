import pika
import json
from pymongo import MongoClient
from datetime import datetime

mongo_client = MongoClient("mongodb://mongo:27017")
db = mongo_client["notes_db"]
events_collection = db["events"]

def callback(ch, method, properties, body):
    event = json.loads(body)

    if isinstance(event.get("timestamp"), str):
        event["timestamp"] = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))

    events_collection.insert_one(event)
    print(f"Event stored: {event['event_type']} for note {event['aggregate_id']}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='note_events', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='note_events', on_message_callback=callback)

    print("Waiting for events. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
