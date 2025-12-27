from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import database and fallback
from app.database import connect_database, close_database, is_using_fallback
from app.fallback import initialize_fallback

# Import routers (we'll create these next)
from app.routers import register, profile, workplace, shift, verify, police

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler - runs on startup and shutdown.
    This replaces the old @app.on_event decorators.
    """
    # STARTUP
    print("=" * 60)
    print("🚀 TRUSTSHIFT Backend Starting...")
    print("=" * 60)
    
    # Try to connect to MongoDB
    mongodb_connected = connect_database()
    
    # If MongoDB fails, initialize fallback
    if not mongodb_connected:
        print("⚠️  MongoDB unavailable - using local JSON fallback")
        initialize_fallback()
    else:
        print("✅ MongoDB connected successfully")
    
    print("=" * 60)
    print("✅ TRUSTSHIFT Backend Ready!")
    print("=" * 60)
    
    yield  # Application runs here
    
    # SHUTDOWN
    print("=" * 60)
    print("🛑 TRUSTSHIFT Backend Shutting Down...")
    close_database()
    print("✅ Shutdown complete")
    print("=" * 60)

# Create FastAPI app
app = FastAPI(
    title="TRUSTSHIFT API",
    description="Real-Time Zero-Trust Workforce Verification System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Root endpoint
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "TRUSTSHIFT API is running",
        "status": "healthy",
        "using_fallback": is_using_fallback()
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """Detailed health check"""
    from app.database import is_connected
    
    return {
        "status": "healthy",
        "database": {
            "mongodb_connected": is_connected(),
            "using_fallback": is_using_fallback()
        },
        "api_version": "1.0.0"
    }

# Include all routers
app.include_router(register.router, prefix="/api", tags=["Registration"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(workplace.router, prefix="/api", tags=["Workplace"])
app.include_router(shift.router, prefix="/api", tags=["Shift"])
app.include_router(verify.router, prefix="/api", tags=["Verification"])
app.include_router(police.router, prefix="/api", tags=["Police"])

# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000