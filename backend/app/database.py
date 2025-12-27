from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "trustshift")

# Global variables
client = None
db = None
connection_status = {"connected": False, "using_fallback": False}

def connect_database():
    """
    Attempts to connect to MongoDB Atlas.
    If connection fails, logs warning and sets fallback flag.
    """
    global client, db, connection_status
    
    try:
        print(f"Attempting to connect to MongoDB at: {MONGODB_URI}")
        
        # Create MongoDB client with timeout
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000
        )
        
        # Test the connection
        client.admin.command('ping')
        
        # Get database
        db = client[DATABASE_NAME]
        
        connection_status["connected"] = True
        connection_status["using_fallback"] = False
        
        print(f"✓ Successfully connected to MongoDB: {DATABASE_NAME}")
        
        # Create indexes for better performance
        _create_indexes()
        
        return True
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"⚠ MongoDB connection failed: {str(e)}")
        print("⚠ Switching to local JSON fallback mode")
        
        connection_status["connected"] = False
        connection_status["using_fallback"] = True
        
        return False
    
    except Exception as e:
        print(f"⚠ Unexpected database error: {str(e)}")
        connection_status["connected"] = False
        connection_status["using_fallback"] = True
        return False

def _create_indexes():
    """Create database indexes for optimal query performance"""
    try:
        # Users collection
        db.users.create_index("uuid", unique=True)
        db.users.create_index("phone")
        
        # Workplace bindings collection
        db.workplace_bindings.create_index("uuid")
        db.workplace_bindings.create_index("supervisor_id")
        
        # Shifts collection
        db.shifts.create_index("shift_id", unique=True)
        db.shifts.create_index("uuid")
        db.shifts.create_index("stt", unique=True)
        db.shifts.create_index([("uuid", 1), ("end", 1)])  # For finding active shifts
        
        # Verifications collection
        db.verifications.create_index("worker_uuid")
        db.verifications.create_index("customer_uuid")
        db.verifications.create_index("time")
        
        print("✓ Database indexes created successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not create indexes: {str(e)}")

def get_database():
    """
    Returns the database instance.
    Used by routers to access collections.
    """
    if not connection_status["connected"]:
        return None
    return db

def is_connected():
    """Check if MongoDB is connected"""
    return connection_status["connected"]

def is_using_fallback():
    """Check if system is using JSON fallback"""
    return connection_status["using_fallback"]

def close_database():
    """Close MongoDB connection gracefully"""
    global client
    if client:
        client.close()
        print("✓ MongoDB connection closed")

# Collections accessors (for convenience)
def get_users_collection():
    """Get users collection"""
    if db is None:
        return None
    return db.users

def get_workplace_bindings_collection():
    """Get workplace_bindings collection"""
    if db is None:
        return None
    return db.workplace_bindings

def get_shifts_collection():
    """Get shifts collection"""
    if db is None:
        return None
    return db.shifts

def get_verifications_collection():
    """Get verifications collection"""
    if db is None:
        return None
    return db.verifications