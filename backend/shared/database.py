"""
MongoDB Database initialization using Motor and Beanie.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

async def init_db():
    """Initialize MongoDB connection and Beanie ODM."""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "ai_business_tycoon")
    
    print(f"🔌 Connecting to MongoDB...")
    print(f"📍 URI: {mongodb_uri[:50]}...{mongodb_uri[-20:]}" if len(mongodb_uri) > 70 else f"📍 URI: {mongodb_uri}")
    print(f"📁 Database: {db_name}")
    
    # Create Motor client
    client = AsyncIOMotorClient(mongodb_uri)
    
    # Test the connection
    try:
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise
    
    # IMPORTANT: We must import our Beanie Document models here so Beanie knows about them
    from services.game.models.player import PlayerState
    
    # Initialize Beanie with the target database and list of document models
    await init_beanie(
        database=client[db_name],
        document_models=[
            PlayerState,
            # Add future document models here (e.g., GlobalMarketState)
        ]
    )
    print(f"✅ Connected to MongoDB ({db_name})")
