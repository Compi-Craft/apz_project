import pika
import json
from pymongo import MongoClient
from datetime import datetime

import consul
import time
consul_client = consul.Consul(host="consul")



def get_members(key):
    data = None
    while data is None:
        index, data = consul_client.kv.get(key)
        time.sleep(5)
    return data['Value'].decode().split(",")

MONGO = get_members("mongo")
RABBIT_MQ = get_members("rabbitmq")
replica_set = "rs0"


mongo_client = MongoClient(
    host=MONGO,
    replicaSet=replica_set,
    serverSelectionTimeoutMS=5000
)

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
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ[0]))
    channel = connection.channel()

    channel.queue_declare(queue='note_events', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='note_events', on_message_callback=callback)

    print("Waiting for events. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
