from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
from datetime import datetime, timezone

app = FastAPI(title="gComm In-Game Commerce API")

# Define the structure of our incoming data (the payload)
class PurchaseEvent(BaseModel):
    user_id: str
    game_id: str
    item_id: str
    price: float
    currency: str = "USD"
    timestamp: str = datetime.now(timezone.utc).isoformat()

def get_rabbitmq_connection():
    # Connect to the RabbitMQ container running on localhost
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    return connection

@app.post("/purchase")
async def process_purchase(event: PurchaseEvent):
    try:
        # 1. Open connection to RabbitMQ
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # 2. Ensure our queue exists before we send data to it
        channel.queue_declare(queue='gcomm_purchases', durable=True)
        
        # 3. Convert our data to a JSON string and publish it to the queue
        channel.basic_publish(
            exchange='',
            routing_key='gcomm_purchases',
            body=json.dumps(event.model_dump()),
            properties=pika.BasicProperties(
                delivery_mode=2, # Make message persistent so it survives broker restarts
            )
        )
        connection.close()
        
        return {"status": "success", "message": "Purchase event queued successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue message: {str(e)}")