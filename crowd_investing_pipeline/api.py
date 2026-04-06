import json
import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
from prometheus_fastapi_instrumentator import Instrumentator

# A dictionary to hold our async connections globally
clients = {}

# The 'lifespan' context manager handles safely opening and closing our database/broker connections
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: Connecting to Redis and Kafka...")
    # 1. Connect to Redis (Replacing GCP Memorystore)
    clients["redis"] = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # 2. Connect to Kafka (Replacing GCP Pub/Sub)
    clients["kafka"] = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    await clients["kafka"].start()
    
    yield # The API runs while suspended here
    
    print("Shutting down: Closing connections...")
    await clients["kafka"].stop()
    await clients["redis"].close()

# Initialize FastAPI
app = FastAPI(title="Crowd-Investing Async API", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
# Define our Investment Payload
class InvestmentEvent(BaseModel):
    user_id: str
    franchise_id: str
    amount: float
    currency: str = "USD"
    timestamp: str = datetime.now(timezone.utc).isoformat()

@app.post("/invest")
async def process_investment(event: InvestmentEvent):
    try:
        # 1. Publish event to Kafka for the data engineers to process later
        await clients["kafka"].send_and_wait("investments_topic", event.model_dump())
        
        # 2. Instantly update the franchise funding total in Redis (so the website UI updates instantly)
        redis_key = f"franchise_total:{event.franchise_id}"
        await clients["redis"].incrbyfloat(redis_key, event.amount)
        
        return {"status": "success", "message": f"Successfully invested ${event.amount} in {event.franchise_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/franchise/{franchise_id}/status")
async def get_franchise_status(franchise_id: str):
    try:
        # Fetch the lightning-fast cached total from Redis
        total = await clients["redis"].get(f"franchise_total:{franchise_id}")
        return {
            "franchise_id": franchise_id,
            "total_funded_usd": float(total) if total else 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))