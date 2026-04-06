import pika
import pymongo
import json
import time
import random
from datetime import datetime, timezone

print("Connecting to MongoDB (Simulated Cosmos DB)...")
# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://admin:adminpassword@localhost:27017/")
db = mongo_client["music_platform"]
users_col = db["users"]

# Clear old data and insert new mock users
users_col.delete_many({})
mock_users = [
    {"user_id": "U101", "name": "Alice", "subscription": "Premium", "country": "USA"},
    {"user_id": "U102", "name": "Bob", "subscription": "Free", "country": "UK"},
    {"user_id": "U103", "name": "Charlie", "subscription": "Premium", "country": "Canada"}
]
users_col.insert_many(mock_users)
print("Inserted mock users into MongoDB!")

print("Connecting to RabbitMQ...")
# Connect to RabbitMQ
credentials = pika.PlainCredentials('admin', 'adminpassword')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()

# Create a queue for our streaming data
channel.queue_declare(queue='listening_history')

songs = ["Bohemian Rhapsody", "Blinding Lights", "Shape of You", "Hotel California", "Smells Like Teen Spirit"]
genres = ["Rock", "Pop", "Pop", "Rock", "Grunge"]

print("Starting the music streaming simulation! Press Ctrl+C to stop.")
try:
    while True:
        # Pick a random user and a random song
        user = random.choice(mock_users)
        song_idx = random.randint(0, len(songs)-1)
        
        # Create the event payload
        event = {
            "event_id": f"EVT-{random.randint(1000, 9999)}",
            "user_id": user["user_id"],
            "song_name": songs[song_idx],
            "genre": genres[song_idx],
            "listen_duration_seconds": random.randint(30, 240),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Send the event to RabbitMQ
        channel.basic_publish(exchange='', routing_key='listening_history', body=json.dumps(event))
        print(f"Streamed: {user['name']} listened to {songs[song_idx]}")
        
        # Wait half a second before the next song
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nSimulation stopped.")
    connection.close()
