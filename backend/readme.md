# TRUSTSHIFT Backend Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [Environment Configuration](#environment-configuration)
5. [File Structure](#file-structure)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Core Components](#core-components)
9. [Data Flow](#data-flow)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Frontend Integration](#frontend-integration)

---

## 🎯 Overview

TRUSTSHIFT Backend is a **FastAPI-based REST API** that powers the Real-Time Zero-Trust Workforce Verification System. It handles:

- **User Registration** (workers, customers, supervisors, police)
- **Workplace Binding** (supervisor assigns workers to workplaces)
- **Shift Management** (start/end shifts, generate QR codes)
- **Worker Verification** (customers scan worker QR codes)
- **Police Verification** (law enforcement checkpoints)
- **Risk Assessment** (dynamic risk scoring)

**Tech Stack:**
- Framework: FastAPI
- Database: MongoDB Atlas (with local JSON fallback)
- Language: Python 3.8+
- Real-time: Polling-based (frontend polls every 3 seconds)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│              (http://localhost:5173)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API (JSON)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                           │
│              (http://localhost:8000)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Routers (API Endpoints)                             │   │
│  │  - register.py   - shift.py                          │   │
│  │  - profile.py    - verify.py                         │   │
│  │  - workplace.py  - police.py                         │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │  Core Logic                                          │   │
│  │  - models.py (Data structures)                       │   │
│  │  - risk_engine.py (Risk scoring)                     │   │
│  │  - database.py (MongoDB connection)                  │   │
│  │  - fallback.py (JSON storage)                        │   │
│  └──────────────────┬───────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
┌────────▼────────┐       ┌────────▼────────┐
│  MongoDB Atlas  │       │  local_fallback │
│  (Production)   │       │     .json       │
│                 │       │  (Development)  │
└─────────────────┘       └─────────────────┘
```

**Key Decisions:**
- **No Authentication Middleware**: Role is chosen at registration, stored in localStorage
- **Polling instead of WebSockets**: Frontend polls `/shift/status` every 3 seconds
- **Dual Storage**: MongoDB Atlas (primary) + JSON fallback (development/resilience)
- **STT (Shift Trust Token)**: Base64-encoded JSON used as QR code data

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- MongoDB Atlas account (or use local JSON fallback)

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `pymongo` - MongoDB driver
- `python-multipart` - File upload support
- `pydantic` - Data validation
- `python-dotenv` - Environment variables
- `dnspython` - MongoDB Atlas DNS resolution

### Step 2: Environment Configuration
Create a `.env` file in the `backend/` directory:

```env
# MongoDB Atlas connection (get from MongoDB Atlas dashboard)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# Database name
DATABASE_NAME=trustshift
```

**If you don't have MongoDB Atlas yet:**
- The system will automatically use local JSON fallback
- You'll see: `⚠ MongoDB unavailable - using local JSON fallback`
- Data will be stored in `backend/app/data/local_fallback.json`

### Step 3: Run the Server
```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Flags explained:**
- `--reload` - Auto-restart on code changes (development only)
- `--host 0.0.0.0` - Accept connections from any IP (required for frontend)
- `--port 8000` - Backend runs on port 8000

### Step 4: Verify Server is Running
Open browser and visit:
- **Health check**: http://localhost:8000
- **API documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Alternative docs**: http://localhost:8000/redoc

You should see:
```json
{
  "message": "TRUSTSHIFT API is running",
  "status": "healthy",
  "using_fallback": true
}
```

---

## 📁 File Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, startup, CORS
│   ├── models.py               # Pydantic models (data structures)
│   ├── database.py             # MongoDB connection & helpers
│   ├── fallback.py             # Local JSON storage (fallback)
│   ├── risk_engine.py          # Risk scoring algorithm
│   │
│   ├── routers/                # API endpoints (routes)
│   │   ├── register.py         # POST /api/register
│   │   ├── profile.py          # GET /api/profile/{uuid}
│   │   ├── workplace.py        # POST /api/workplace/bind
│   │   ├── shift.py            # POST /api/shift/start, /end, GET /status
│   │   ├── verify.py           # POST /api/verify/worker
│   │   └── police.py           # POST /api/police/scan
│   │
│   └── data/                   # Auto-created directory
│       └── local_fallback.json # JSON storage (created automatically)
│
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (create this)
```

---

## 🗄️ Database Schema

### Collections Overview

| Collection | Purpose | Primary Key |
|------------|---------|-------------|
| `users` | All registered users | `uuid` |
| `workplace_bindings` | Worker-workplace relationships | `uuid` (worker) |
| `shifts` | Active and historical shifts | `shift_id` |
| `verifications` | Customer scan logs | No primary key |

### 1. Users Collection
```javascript
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",  // Unique ID
  "role": "worker",                                 // worker|customer|supervisor|police
  "name": "John Doe",
  "phone": "+919876543210",
  "face_hash": "a1b2c3...",                         // SHA-256 hash (never raw image)
  "id_hash": "d4e5f6...",                           // SHA-256 hash (never raw ID)
  "platform_links": ["zomato", "swiggy"],
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

**Indexes:**
- `uuid` (unique)
- `phone`

### 2. Workplace Bindings Collection
```javascript
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",  // Worker UUID
  "workplace": "Zomato Warehouse 5",
  "location": "Delhi NCR - Sector 18",
  "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
  "active": true,
  "created_at": "2025-01-15T11:00:00.000Z"
}
```

**Indexes:**
- `uuid` (worker)
- `supervisor_id`

**Business Rules:**
- One worker can have only ONE active binding at a time
- Worker cannot start shift without active binding
- Supervisor must be the one who created the binding

### 3. Shifts Collection
```javascript
{
  "shift_id": "770g0622-g40d-63f6-c938-668877662222",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",  // Worker UUID
  "start": "2025-01-15T09:00:00.000Z",
  "end": null,                                      // null = active shift
  "stt": "eyJzaGlmdF9pZCI6Ijc3MGcwNjIyLWc0MGQtNjNmNi1jOTM4LTY2ODg3NzY2MjIyMiIsIndvcmtlcl91dWlkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwid29ya3BsYWNlIjoiWm9tYXRvIFdhcmVob3VzZSA1Iiwic3RhcnRfdGltZSI6IjIwMjUtMDEtMTVUMDk6MDA6MDAuMDAwWiIsImlzc3VlZF9hdCI6IjIwMjUtMDEtMTVUMDk6MDA6MDIuMDAwWiJ9",  // Base64 JSON
  "risk_state": "green",                            // green|yellow|red
  "workplace": "Zomato Warehouse 5",
  "supervisor_id": "660f9511-f39c-52e5-b827-557766551111"
}
```

**Indexes:**
- `shift_id` (unique)
- `uuid` (worker)
- `stt` (unique)
- `uuid + end` (compound index for finding active shifts)

**STT (Shift Trust Token) Format:**
```javascript
// Decoded STT contains:
{
  "shift_id": "770g0622-g40d-63f6-c938-668877662222",
  "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "workplace": "Zomato Warehouse 5",
  "start_time": "2025-01-15T09:00:00.000Z",
  "issued_at": "2025-01-15T09:00:02.000Z"
}
```

### 4. Verifications Collection
```javascript
{
  "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "customer_uuid": "880h1733-h51e-74g7-d049-779988773333",
  "time": "2025-01-15T14:30:00.000Z",
  "location": null  // Optional: GPS coordinates
}
```

**Indexes:**
- `worker_uuid`
- `customer_uuid`
- `time`

**Purpose:** Creates two-sided accountability. Every customer scan is logged, protecting both worker and customer.

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api
```

### Health Check
```http
GET /
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": {
    "mongodb_connected": true,
    "using_fallback": false
  },
  "api_version": "1.0.0"
}
```

---

### 1. Registration

#### Register User
```http
POST /api/register
Content-Type: application/json

{
  "role": "worker",                    // worker|customer|supervisor|police
  "name": "John Doe",
  "phone": "+919876543210",
  "face_image": "base64_encoded_string",  // Optional: face capture
  "id_image": "base64_encoded_string",    // Optional: govt ID
  "platform_link": "zomato"               // Optional: gig platform
}
```

**Success Response (201):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "role": "worker",
  "verification_status": "pending",
  "message": "Registration successful as worker"
}
```

**Error Responses:**
- `400` - Invalid data (missing name/phone)
- `409` - Phone already registered
- `500` - Database error

**Frontend Action:**
```javascript
// Store in localStorage
localStorage.setItem('uuid', response.uuid);
localStorage.setItem('role', response.role);
// Redirect to dashboard
window.location.href = `/${response.role}`;
```

#### Check Phone Registration
```http
GET /api/register/check/{phone}
```

**Response:**
```json
{
  "registered": true,
  "role": "worker",
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. Profile

#### Get User Profile
```http
GET /api/profile/{uuid}
```

**Worker Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "role": "worker",
  "name": "John Doe",
  "phone": "+919876543210",
  "platform_links": ["zomato"],
  "created_at": "2025-01-15T10:30:00.000Z",
  "worker_data": {
    "workplace_binding": {
      "workplace": "Zomato Warehouse 5",
      "location": "Delhi NCR - Sector 18",
      "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
      "bound_at": "2025-01-15T11:00:00.000Z"
    },
    "shift_history": [...],
    "total_shifts": 45,
    "verification_count": 328
  }
}
```

**Customer Response:**
```json
{
  "uuid": "880h1733-h51e-74g7-d049-779988773333",
  "role": "customer",
  "name": "Jane Smith",
  "phone": "+919123456789",
  "created_at": "2025-01-10T08:00:00.000Z",
  "customer_data": {
    "verification_history": [...],
    "total_verifications": 12
  }
}
```

#### Get Worker Shifts
```http
GET /api/profile/{uuid}/shifts?limit=20
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "shifts": [
    {
      "shift_id": "770g0622-g40d-63f6-c938-668877662222",
      "start": "2025-01-15T09:00:00.000Z",
      "end": "2025-01-15T17:00:00.000Z",
      "workplace": "Zomato Warehouse 5",
      "risk_state": "green"
    }
  ],
  "count": 20
}
```

---

### 3. Workplace

#### Bind Worker to Workplace
```http
POST /api/workplace/bind
Content-Type: application/json

{
  "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "workplace": "Zomato Warehouse 5",
  "location": "Delhi NCR - Sector 18",
  "supervisor_id": "660f9511-f39c-52e5-b827-557766551111"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Worker John Doe bound to Zomato Warehouse 5",
  "binding": {
    "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "worker_name": "John Doe",
    "workplace": "Zomato Warehouse 5",
    "location": "Delhi NCR - Sector 18",
    "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
    "supervisor_name": "Manager Name",
    "created_at": "2025-01-15T11:00:00.000Z"
  }
}
```

**Error Responses:**
- `400` - Invalid data, worker not found, or wrong role
- `404` - Worker or supervisor not found
- `409` - Worker already has active binding

#### Get Supervisor's Bindings
```http
GET /api/workplace/bindings/{supervisor_id}
```

**Response:**
```json
{
  "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
  "supervisor_name": "Manager Name",
  "bindings": [
    {
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "worker_name": "John Doe",
      "workplace": "Zomato Warehouse 5",
      "location": "Delhi NCR - Sector 18",
      "active": true,
      "created_at": "2025-01-15T11:00:00.000Z"
    }
  ],
  "count": 1
}
```

#### Get Worker's Binding
```http
GET /api/workplace/binding/{worker_uuid}
```

**Response:**
```json
{
  "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "has_binding": true,
  "binding": {
    "workplace": "Zomato Warehouse 5",
    "location": "Delhi NCR - Sector 18",
    "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
    "active": true
  }
}
```

---

### 4. Shift Management

#### Start Shift
```http
POST /api/shift/start
Content-Type: application/json

{
  "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
  "workplace": "Zomato Warehouse 5"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Shift started for John Doe",
  "shift": {
    "shift_id": "770g0622-g40d-63f6-c938-668877662222",
    "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "worker_name": "John Doe",
    "workplace": "Zomato Warehouse 5",
    "supervisor_id": "660f9511-f39c-52e5-b827-557766551111",
    "start": "2025-01-15T09:00:00.000Z",
    "stt": "eyJzaGlmdF9pZCI6Ijc3MGcwNjIy...",  // Base64 QR code data
    "risk_state": "green"
  }
}
```

**Error Responses:**
- `400` - Worker not bound to workplace, or wrong workplace
- `404` - Worker/supervisor not found
- `409` - Worker already has active shift

**Frontend Action:**
```javascript
// Worker dashboard polls this STT and displays as QR code
const qrCodeData = response.shift.stt;
generateQRCode(qrCodeData);
```

#### End Shift
```http
POST /api/shift/end
Content-Type: application/json

{
  "shift_id": "770g0622-g40d-63f6-c938-668877662222",
  "supervisor_id": "660f9511-f39c-52e5-b827-557766551111"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Shift ended successfully",
  "shift_id": "770g0622-g40d-63f6-c938-668877662222",
  "end_time": "2025-01-15T17:00:00.000Z"
}
```

#### Get Shift Status (POLLED EVERY 3 SECONDS)
```http
GET /api/shift/status/{worker_uuid}
```

**Active Shift Response:**
```json
{
  "active": true,
  "shift_id": "770g0622-g40d-63f6-c938-668877662222",
  "stt": "eyJzaGlmdF9pZCI6Ijc3MGcwNjIy...",
  "risk_state": "green",
  "start_time": "2025-01-15T09:00:00.000Z",
  "workplace": "Zomato Warehouse 5"
}
```

**No Active Shift Response:**
```json
{
  "active": false,
  "shift_id": null,
  "stt": null,
  "risk_state": null,
  "start_time": null,
  "workplace": null
}
```

**Frontend Polling:**
```javascript
// Worker dashboard
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/shift/status/${workerUUID}`);
    const data = await response.json();
    
    if (data.active) {
      setQRCode(data.stt);  // Show QR code
      setRiskColor(data.risk_state);
    } else {
      setQRCode(null);  // Hide QR code
    }
  }, 3000);  // Poll every 3 seconds
  
  return () => clearInterval(interval);
}, [workerUUID]);
```

---

### 5. Verification (Customer Scanning)

#### Verify Worker
```http
POST /api/verify/worker
Content-Type: application/json

{
  "stt": "eyJzaGlmdF9pZCI6Ijc3MGcwNjIy...",  // Scanned QR code
  "customer_uuid": "880h1733-h51e-74g7-d049-779988773333"
}
```

**Success Response (200):**
```json
{
  "verified": true,
  "worker_name": "John Doe",
  "worker_photo": "a1b2c3...",  // Hash reference
  "employer": "Zomato Warehouse 5",
  "shift_active": true,
  "risk_color": "green",
  "message": "Worker verified successfully"
}
```

**Failed Verification:**
```json
{
  "verified": false,
  "worker_name": null,
  "worker_photo": null,
  "employer": null,
  "shift_active": false,
  "risk_color": null,
  "message": "Worker's shift has ended"
}
```

#### Get Customer Verification History
```http
GET /api/verify/history/{customer_uuid}?limit=20
```

#### Get Worker Verification Stats
```http
GET /api/verify/stats/{worker_uuid}
```

---

### 6. Police Verification

#### Police Scan Worker
```http
POST /api/police/scan
Content-Type: application/json

{
  "stt": "eyJzaGlmdF9pZCI6Ijc3MGcwNjIy...",
  "officer_uuid": "990i2844-i62f-85h8-e150-880099884444"
}
```

**Success Response (200):**
```json
{
  "verified": true,
  "identity": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "phone": "+919876543210",
    "role": "worker",
    "registered_at": "2025-01-15T10:30:00.000Z",
    "platform_links": ["zomato"]
  },
  "workplace": {
    "name": "Zomato Warehouse 5",
    "location": "Delhi NCR - Sector 18",
    "bound_at": "2025-01-15T11:00:00.000Z",
    "binding_active": true
  },
  "shift_status": {
    "active": true,
    "shift_id": "770g0622-g40d-63f6-c938-668877662222",
    "start_time": "2025-01-15T09:00:00.000Z",
    "end_time": null,
    "duration_hours": 5.5
  },
  "risk_state": "green",
  "supervisor_name": "Manager Name",
  "message": "Worker verified - All details validated"
}
```

#### Get Recent Events
```http
GET /api/police/events?limit=50
```

#### Get Active Workers
```http
GET /api/police/active-workers
```

**Response:**
```json
{
  "active_workers": [
    {
      "worker_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "worker_name": "John Doe",
      "worker_phone": "+919876543210",
      "workplace": "Zomato Warehouse 5",
      "shift_start": "2025-01-15T09:00:00.000Z",
      "risk_state": "green",
      "shift_duration_hours": 5.5
    }
  ],
  "count": 1
}
```

---

## ⚙️ Core Components

### 1. models.py
**Purpose:** Define all data structures using Pydantic

**Key Models:**
- `UserRole` - Enum: worker, customer, supervisor, police
- `RiskState` - Enum: green, yellow, red
- `RegisterRequest/Response` - Registration data
- `ShiftStartRequest`, `ShiftStatusResponse` - Shift management
- `VerifyWorkerRequest/Response` - Worker verification
- `PoliceScanRequest/Response` - Police scanning

**Example:**
```python
from app.models import UserRole, RegisterRequest

# Frontend sends:
request = RegisterRequest(
    role=UserRole.WORKER,
    name="John Doe",
    phone="+919876543210"
)
```

### 2. database.py
**Purpose:** MongoDB Atlas connection and collection access

**Key Functions:**
- `connect_database()` - Called at startup, tries MongoDB
- `get_database()` - Returns db instance
- `is_connected()` - Check MongoDB status
- `is_using_fallback()` - Check if using JSON
- `get_users_collection()`, `get_shifts_collection()`, etc.

**Connection Flow:**
```
Startup → connect_database()
    ↓
MongoDB Atlas available?
    ├─ YES → Use MongoDB
    └─ NO → Switch to JSON fallback
```

### 3. fallback.py
**Purpose:** Local JSON storage when MongoDB unavailable

**Key Functions:**
- `initialize_fallback()` - Load data from JSON
- `insert_user()`, `find_user_by_uuid()` - User operations
- `insert_shift()`, `find_active_shift()` - Shift operations
- `insert_verification()` - Verification logging

**Storage Location:**
```
backend/app/data/local_fallback.json
```

**Auto-save:** Every write operation automatically saves to file

### 4. risk_engine.py
**Purpose:** Calculate risk scores for workers

**Algorithm:**
```
Risk Score (0-100) = 
  Time Risk (0-30)       +  // Late night = 30
  Zone Risk (0-25)       +  // High-crime area = 25
  Complaint Risk (0-30)  +  // 3+ complaints = 30
  Account Age Risk (0-15)   // <7 days = 15

Risk State:
  0-30   = GREEN   (low risk, no restrictions)
  31-60  = YELLOW  (medium risk, cannot serve minors)
  61-100 = RED     (high risk, severe restrictions)
```

**Key Functions:**
- `calculate_risk_score()` - Main scoring function
- `get_risk_state()` - Convert score to color
- `should_restrict_allocation()` - Check if worker restricted

**Usage in Shift Start:**
```python
risk_score = calculate_risk_score(
    worker_data=worker,
    current_time=datetime.utcnow(),
    location_zone="sector_18_delhi",
    complaint_count=0
)
risk_state = get_risk_state(risk_score)  # "green"
```

### 5. Routers (API Endpoints)
Each router file handles specific functionality:

| Router | Purpose | Main Endpoints |
|--------|---------|----------------|
| `register.py` | User registration | POST /register |
| `profile.py` | User profiles | GET /profile/{uuid} |
| `workplace.py` | Workplace binding | POST /workplace/bind |
| `shift.py` | Shift management | POST /shift/start, GET /shift/status |
| `verify.py` | Customer verification | POST /verify/worker |
| `police.py` | Police scanning | POST /police/scan |

---

## 🔄 Data Flow

### Scenario 1: Worker Shift Activation

```
1. Supervisor Dashboard
   └─> POST /api/shift/start
       {worker_uuid, supervisor_id, workplace}

2. Backend Validates:
   ├─> Worker exists? ✓
   ├─> Has workplace binding? ✓
   ├─> No active shift? ✓
   └─> Calculate risk score

3. Backend Creates:
   ├─> Generate shift_id
   ├─> Generate STT (base64 JSON)
   └─> Store in shifts collection

4. Backend Returns:
   └─> {shift_id, stt, risk_state}

5. Worker Dashboard (polling every 3s)
   └─> GET /api/shift/status/{worker_uuid}
       ├─> Returns: {active: true, stt: "..."}
       └─> Display QR code with STT

6. Shift Active!
   Worker QR code now visible
```

### Scenario 2: Customer Verification

```
1. Customer Scans QR Code
   └─> Reads STT (base64 string)

2. Customer Dashboard
   └─> POST /api/verify/worker
       {stt, customer_uuid}

3. Backend Process:
   ├─> Decode STT → extract shift_id, worker_uuid
   ├─> Find shift by STT
   ├─> Check shift.end == null (active?)
   ├─> Get worker details
   └─> Log verification

4. Backend Returns:
   └─> {
         verified: true,
         worker_name: "John Doe",
         employer: "Zomato Warehouse 5",
         shift_active: true,
         risk_color: "green"
       }

5. Customer Sees Verification Card
   ✓ Name verified
   ✓ Employer verified
   ✓ Shift active
   ✓ Risk: Green
```

### Scenario 3: Police Checkpoint

```
1. Officer Scans Worker QR
   └─> Reads STT

2. Police Dashboard
   └─> POST /api/police/scan
       {stt, officer_uuid}

3. Backend Returns EXTENDED Data:
   ├─> Full identity (name, phone, UUID)
   ├─> Workplace details (location, binding)
   ├─> Shift timing (start, duration)
   ├─> Risk assessment
   └─> Supervisor contact

4. Officer Decision
   ├─> Green + Valid → Allow passage
   ├─> Yellow → Extra verification
   └─> Red + Suspicious → Detain/investigate
```

---

## 🧪 Testing

### Manual Testing with Swagger UI

1. **Start Server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open Swagger UI:**
   ```
   http://localhost:8000/docs
   ```

3. **Test Registration Flow:**
   ```
   Step 1: POST /api/register (create worker)
   Step 2: POST /api/register (create supervisor)
   Step 3: POST /api/register (create customer)
   Step 4: GET /api/profile/{uuid} (verify created)
   ```

4. **Test Shift Flow:**
   ```
   Step 1: POST /api/workplace/bind (bind worker to workplace)
   Step 2: POST /api/shift/start (start shift)
   Step 3: GET /api/shift/status/{worker_uuid} (verify active)
   Step 4: POST /api/verify/worker (customer scans)
   Step 5: POST /api/shift/end (end shift)
   Step 6: GET /api/shift/status/{worker_uuid} (verify inactive)
   ```

### Testing with cURL

**Register a worker:**
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "role": "worker",
    "name": "John Doe",
    "phone": "+919876543210",
    "face_image": "test_hash",
    "id_image": "test_hash"
  }'
```

**Check shift status:**
```bash
curl http://localhost:8000/api/shift/status/YOUR_WORKER_UUID
```

### Testing with Python requests

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Register worker
response = requests.post(f"{BASE_URL}/register", json={
    "role": "worker",
    "name": "Test Worker",
    "phone": "+919999999999",
    "face_image": "hash123",
    "id_image": "hash456"
})
worker_data = response.json()
worker_uuid = worker_data["uuid"]
print(f"Worker registered: {worker_uuid}")

# Get profile
profile = requests.get(f"{BASE_URL}/profile/{worker_uuid}").json()
print(f"Worker name: {profile['name']}")
```

---

## 🐛 Troubleshooting

### Issue 1: Import Errors (pymongo, fastapi, etc.)
**Symptom:** VS Code shows red underlines, "Import could not be resolved"

**Solution:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# If using virtual environment:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Issue 2: MongoDB Connection Failed
**Symptom:** 
```
⚠ MongoDB connection failed: [SSL: CERTIFICATE_VERIFY_FAILED]
⚠ Switching to local JSON fallback mode
```

**Solutions:**

**Option A: Use JSON Fallback (Recommended for Development)**
- No action needed! System automatically uses local JSON
- Data stored in `backend/app/data/local_fallback.json`
- Perfect for testing without MongoDB Atlas

**Option B: Fix MongoDB Atlas Connection**
1. Verify `.env` file exists in `backend/` directory
2. Check `MONGODB_URI` format:
   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```
3. Ensure MongoDB Atlas allows connections from your IP:
   - Go to MongoDB Atlas → Network Access
   - Add IP Address → Add Current IP Address
4. Check database user has read/write permissions

### Issue 3: CORS Errors from Frontend
**Symptom:** 
```
Access to fetch at 'http://localhost:8000/api/register' from origin 
'http://localhost:5173' has been blocked by CORS policy
```

**Solution:**
Check `main.py` has correct CORS origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If frontend runs on different port, add it here.

### Issue 4: Server Won't Start
**Symptom:**
```
ERROR:    [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Issue 5: Shift Status Always Returns `active: false`
**Symptom:** Worker dashboard never shows QR code

**Debug Steps:**
1. **Check if shift was created:**
   ```bash
   curl http://localhost:8000/api/shift/status/WORKER_UUID
   ```

2. **Verify shift_id in database:**
   - MongoDB: Check `shifts` collection
   - JSON: Open `backend/app/data/local_fallback.json`

3. **Common causes:**
   - Shift was never started (supervisor didn't click "Start Shift")
   - Shift was ended (supervisor clicked "End Shift")
   - Worker UUID mismatch (frontend using wrong UUID)

### Issue 6: Customer Verification Fails
**Symptom:** "QR code not found or invalid"

**Debug Steps:**
1. **Check STT format:**
   ```python
   import base64, json
   stt = "eyJzaGlmdF9pZCI6..." # Your STT
   decoded = base64.b64decode(stt).decode()
   print(json.loads(decoded))
   ```

2. **Verify shift exists:**
   ```bash
   curl http://localhost:8000/api/shift/status/WORKER_UUID
   ```

3. **Common causes:**
   - QR code contains corrupted data
   - Shift was ended after QR was generated
   - Customer UUID is invalid

### Issue 7: Risk Score Always 0 or 100
**Symptom:** All workers show same risk color

**Debug:**
Check `risk_engine.py` is being called correctly:
```python
# In shift.py, during shift start:
risk_score = calculate_risk_score(
    worker_data=worker,  # ← Must be full worker dict
    current_time=datetime.utcnow(),
    location_zone=binding.get("location"),  # ← Must have location
    complaint_count=0
)
```

### Issue 8: Data Not Persisting After Server Restart
**Symptom:** All users/shifts disappear when server restarts

**If using MongoDB:**
- Data SHOULD persist (stored in cloud)
- Check MongoDB Atlas → Collections → Verify data exists

**If using JSON fallback:**
- Data SHOULD persist (stored in `local_fallback.json`)
- Check file exists: `backend/app/data/local_fallback.json`
- Check file is not empty
- Check file permissions (must be writable)

---

## 🔗 Frontend Integration

### CORS Setup (Already Done)
Backend allows frontend connections from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (Alternative)

### API Base URL
Frontend should use:
```javascript
const API_BASE_URL = "http://localhost:8000/api";
```

### Example API Calls from Frontend

#### 1. Registration
```javascript
// src/api/client.js
export async function registerUser(data) {
  const response = await fetch(`${API_BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }
  
  return response.json();
}

// Usage in component
const handleRegister = async () => {
  try {
    const result = await registerUser({
      role: 'worker',
      name: 'John Doe',
      phone: '+919876543210',
      face_image: faceImageBase64,
      id_image: idImageBase64
    });
    
    localStorage.setItem('uuid', result.uuid);
    localStorage.setItem('role', result.role);
    navigate(`/${result.role}`);
  } catch (error) {
    alert(error.message);
  }
};
```

#### 2. Polling Shift Status
```javascript
// Worker dashboard component
import { useState, useEffect } from 'react';

function WorkerHome() {
  const [shiftStatus, setShiftStatus] = useState(null);
  const workerUUID = localStorage.getItem('uuid');

  useEffect(() => {
    // Poll every 3 seconds
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/shift/status/${workerUUID}`
        );
        const data = await response.json();
        setShiftStatus(data);
      } catch (error) {
        console.error('Failed to fetch shift status:', error);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [workerUUID]);

  return (
    <div>
      {shiftStatus?.active ? (
        <QRCode value={shiftStatus.stt} />
      ) : (
        <p>No active shift</p>
      )}
    </div>
  );
}
```

#### 3. Worker Verification
```javascript
// Customer dashboard
const handleScan = async (scannedSTT) => {
  const customerUUID = localStorage.getItem('uuid');
  
  try {
    const response = await fetch(`${API_BASE_URL}/verify/worker`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stt: scannedSTT,
        customer_uuid: customerUUID
      })
    });
    
    const result = await response.json();
    
    if (result.verified) {
      showVerificationCard({
        name: result.worker_name,
        employer: result.employer,
        risk: result.risk_color
      });
    } else {
      alert(result.message);
    }
  } catch (error) {
    alert('Verification failed');
  }
};
```

#### 4. Start Shift (Supervisor)
```javascript
const handleStartShift = async (workerUUID, workplace) => {
  const supervisorUUID = localStorage.getItem('uuid');
  
  try {
    const response = await fetch(`${API_BASE_URL}/shift/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        worker_uuid: workerUUID,
        supervisor_id: supervisorUUID,
        workplace: workplace
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      alert(`Shift started for ${result.shift.worker_name}`);
    }
  } catch (error) {
    alert('Failed to start shift');
  }
};
```

### Error Handling Best Practices

```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    // Check for HTTP errors
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    // Network error or parsing error
    console.error('API call failed:', error);
    throw error;
  }
}

// Usage
try {
  const data = await apiCall('/profile/123');
  console.log(data);
} catch (error) {
  alert(`Error: ${error.message}`);
}
```

### Expected Response Times
- Registration: 100-300ms
- Profile fetch: 50-150ms
- Shift status (polling): 30-100ms
- Verification: 100-200ms
- Workplace binding: 150-300ms

---

## 📊 Performance Considerations

### Database Indexes (Already Created)
```python
# Automatically created by database.py
users: uuid (unique), phone
workplace_bindings: uuid, supervisor_id
shifts: shift_id (unique), stt (unique), uuid + end (compound)
verifications: worker_uuid, customer_uuid, time
```

### Polling Optimization
**Current:** Frontend polls `/shift/status` every 3 seconds

**Why not WebSockets?**
- Simpler implementation for MVP
- Works with standard HTTP infrastructure
- No persistent connection management
- Easier debugging

**Future optimization:**
- Implement WebSocket connections
- Push shift updates to worker
- Reduce polling to 5-10 seconds for non-critical updates

### Caching Strategy
**Current:** No caching (direct database queries)

**Future optimization:**
- Redis cache for active shifts
- Cache worker profiles (expire after 1 hour)
- Cache verification counts

---

## 🔒 Security Notes

### What's Implemented
1. **Biometric Hashing:** Face/ID images are SHA-256 hashed, never stored raw
2. **STT Encoding:** Base64 encoding prevents tampering (in production, add HMAC signature)
3. **Role Validation:** All endpoints verify user roles
4. **Input Validation:** Pydantic models validate all inputs

### What's NOT Implemented (MVP Limitations)
1. **No JWT/Session Auth:** Role stored in localStorage (not secure)
2. **No Password Protection:** No login required
3. **No Rate Limiting:** Can be abused
4. **No Encryption:** STT is base64, not encrypted
5. **No IP Whitelisting:** Anyone can access API

### Production Security Checklist
- [ ] Add JWT authentication
- [ ] Add password hashing (bcrypt)
- [ ] Add rate limiting (slowapi)
- [ ] Add HTTPS/TLS
- [ ] Add request signing for STT
- [ ] Add CAPTCHA for registration
- [ ] Add audit logging
- [ ] Add input sanitization
- [ ] Add SQL injection prevention (already done via MongoDB)
- [ ] Add CORS restriction (specific domains only)

---

## 📈 Monitoring & Logging

### Current Logging
Backend prints to console:
```
✓ Successfully connected to MongoDB: trustshift
✓ Database indexes created successfully
✓ TRUSTSHIFT Backend Ready!
```

### Viewing Logs
```bash
# Run server with logging
uvicorn app.main:app --reload --log-level info

# Common log messages:
# - ✓ MongoDB connected
# - ⚠ MongoDB unavailable - using fallback
# - ⚠ Could not create indexes
# - Registration error: ...
# - Shift start error: ...
```

### Production Logging Setup
```python
# Add to main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trustshift.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Set up production MongoDB Atlas cluster
- [ ] Configure `.env` with production credentials
- [ ] Remove `--reload` flag from uvicorn command
- [ ] Set up HTTPS certificate
- [ ] Configure firewall rules
- [ ] Set up backup strategy for database
- [ ] Add authentication middleware
- [ ] Add rate limiting
- [ ] Configure monitoring (e.g., Datadog, New Relic)
- [ ] Set up error tracking (e.g., Sentry)

### Production Run Command
```bash
# Production (no reload, specific host)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn (recommended)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📞 Support & Contact

**For Your Teammate (Frontend Developer):**

### Quick Reference
- **Backend URL:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

### Common Questions

**Q: How do I test if backend is running?**
```bash
curl http://localhost:8000
# Should return: {"message": "TRUSTSHIFT API is running", ...}
```

**Q: What's the UUID?**
A: Unique user ID returned by `/api/register`. Store it in `localStorage` on frontend.

**Q: How does QR code work?**
A: Worker polls `/api/shift/status/{uuid}` every 3 seconds. When `active: true`, display `stt` as QR code.

**Q: Why does customer scan fail?**
A: Most common: shift was ended by supervisor, or customer UUID is invalid.

**Q: Can I test without frontend?**
A: Yes! Use Swagger UI at `http://localhost:8000/docs`

### Files Summary
| File | Purpose | You Need To |
|------|---------|-------------|
| `main.py` | App setup, CORS | Know API base URL |
| `models.py` | Data structures | Match JSON structure |
| `register.py` | POST /register | Store uuid & role |
| `shift.py` | Shift management | Poll /shift/status |
| `verify.py` | Customer scan | Send STT from QR |
| `police.py` | Police scan | Same as verify but more data |

---

## 🎓 Learning Resources

### FastAPI Documentation
- Official Docs: https://fastapi.tiangolo.com
- Tutorial: https://fastapi.tiangolo.com/tutorial/

### MongoDB with Python
- PyMongo Tutorial: https://pymongo.readthedocs.io/en/stable/tutorial.html
- MongoDB Atlas: https://www.mongodb.com/docs/atlas/

### Pydantic Models
- Pydantic Docs: https://docs.pydantic.dev/latest/

---

## 📝 Change Log

### Version 1.0.0 (Current)
- ✅ User registration (4 roles)
- ✅ Workplace binding
- ✅ Shift management with STT
- ✅ Risk scoring engine
- ✅ Customer verification
- ✅ Police verification
- ✅ MongoDB Atlas + JSON fallback
- ✅ CORS configuration
- ✅ API documentation (Swagger)

### Planned Features (Future)
- [ ] JWT authentication
- [ ] WebSocket real-time updates
- [ ] Complaint system
- [ ] SMS notifications
- [ ] GPS location tracking
- [ ] Photo upload & storage
- [ ] Advanced analytics dashboard
- [ ] Multi-language support

---

## ✅ Final Setup Verification

Run this checklist to ensure everything works:

```bash
# 1. Dependencies installed?
pip list | grep fastapi
pip list | grep pymongo

# 2. Server starts?
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Health check passes?
curl http://localhost:8000/health

# 4. Can register user?
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"role":"worker","name":"Test","phone":"+919999999999"}'

# 5. Swagger UI loads?
# Open: http://localhost:8000/docs

# 6. Frontend can connect?
# From frontend, try: fetch('http://localhost:8000')
```

---

**🎉 Backend Setup Complete!**

Your TRUSTSHIFT backend is now ready for frontend integration. Share this README with your teammate and start building the React frontend!