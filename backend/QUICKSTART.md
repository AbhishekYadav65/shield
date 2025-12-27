# TRUSTSHIFT Backend - Quick Start Guide

**For your teammate who needs to get backend running in 5 minutes.**

---

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 minute)
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start Server (30 seconds)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify Running (30 seconds)
Open browser: http://localhost:8000

Should see:
```json
{
  "message": "TRUSTSHIFT API is running",
  "status": "healthy",
  "using_fallback": true
}
```

**✅ Done! Backend is running.**

---

## 🔧 Frontend Integration

### API Base URL
```javascript
const API_BASE_URL = "http://localhost:8000/api";
```

### Test Connection from Frontend
```javascript
fetch('http://localhost:8000')
  .then(res => res.json())
  .then(data => console.log('Backend connected:', data))
  .catch(err => console.error('Backend not running:', err));
```

---

## 📚 Essential Endpoints

### 1. Register User
```javascript
POST http://localhost:8000/api/register
{
  "role": "worker",
  "name": "John Doe",
  "phone": "+919876543210"
}
// Returns: {uuid, role, message}
// Store uuid in localStorage!
```

### 2. Get Profile
```javascript
GET http://localhost:8000/api/profile/{uuid}
// Returns full user profile
```

### 3. Start Shift (Supervisor)
```javascript
POST http://localhost:8000/api/shift/start
{
  "worker_uuid": "...",
  "supervisor_id": "...",
  "workplace": "Warehouse 5"
}
// Returns: {shift_id, stt, risk_state}
```

### 4. Check Shift Status (Worker - Poll Every 3s)
```javascript
GET http://localhost:8000/api/shift/status/{worker_uuid}
// Returns: {active: true, stt: "...", risk_state: "green"}
// Display STT as QR code when active=true
```

### 5. Verify Worker (Customer Scans QR)
```javascript
POST http://localhost:8000/api/verify/worker
{
  "stt": "eyJzaGlmdF9pZCI6...",  // from QR code
  "customer_uuid": "..."
}
// Returns: {verified: true, worker_name, employer, risk_color}
```

---

## 🎯 Interactive API Docs

**Swagger UI:** http://localhost:8000/docs

- Test all endpoints
- See request/response examples
- Try API calls without code

---

## 🐛 Common Issues

### Issue: "Import fastapi could not be resolved"
```bash
pip install -r requirements.txt
```

### Issue: "Address already in use"
```bash
# Kill process on port 8000
lsof -i :8000  # Mac/Linux
kill -9 <PID>

netstat -ano | findstr :8000  # Windows
taskkill /PID <PID> /F
```

### Issue: CORS error from frontend
Check frontend runs on:
- `http://localhost:5173` (Vite)
- `http://localhost:3000` (CRA)

Backend allows both (already configured).

### Issue: "MongoDB connection failed"
**Solution:** Ignore it! Backend automatically uses local JSON fallback.
```
⚠ MongoDB unavailable - using local JSON fallback
```
This is NORMAL for development. Data stored in:
```
backend/app/data/local_fallback.json
```

---

## 📱 Testing Full Flow

### Test 1: Registration
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "role": "worker",
    "name": "Test Worker",
    "phone": "+919999999999"
  }'
```

Copy the returned `uuid`.

### Test 2: Get Profile
```bash
curl http://localhost:8000/api/profile/YOUR_UUID_HERE
```

### Test 3: Shift Flow
1. Register supervisor
2. Bind worker to workplace
3. Start shift
4. Check shift status
5. Worker shows QR code
6. Customer scans & verifies

---

## 💡 Key Concepts

### UUID
- Unique user ID
- Returned by `/api/register`
- **Frontend must store in localStorage**
- Used in all subsequent API calls

### STT (Shift Trust Token)
- Base64-encoded string
- Contains: shift_id, worker_uuid, workplace
- Generated when shift starts
- **This is the QR code data**
- Worker displays as QR
- Customer/Police scan to verify

### Polling
Worker dashboard must poll every 3 seconds:
```javascript
setInterval(() => {
  fetch(`/api/shift/status/${uuid}`)
    .then(res => res.json())
    .then(data => {
      if (data.active) showQR(data.stt);
      else hideQR();
    });
}, 3000);
```

### Risk Colors
- 🟢 **Green** (0-30): Low risk, no restrictions
- 🟡 **Yellow** (31-60): Medium risk, some restrictions
- 🔴 **Red** (61-100): High risk, severe restrictions

---

## 📞 Need Help?

1. **Check server is running:** http://localhost:8000
2. **Check API docs:** http://localhost:8000/docs
3. **Check logs in terminal** where uvicorn is running
4. **Read full README:** `BACKEND_README.md`

---

## ✅ Quick Verification Checklist

- [ ] `pip install -r requirements.txt` completed
- [ ] Server starts without errors
- [ ] http://localhost:8000 returns JSON
- [ ] http://localhost:8000/docs shows Swagger UI
- [ ] Can register a user via Swagger UI
- [ ] Frontend can fetch from localhost:8000

**All checked? You're ready to integrate!**

---

**Backend Port:** 8000  
**Frontend Port:** 5173 (Vite) or 3000  
**API Base:** http://localhost:8000/api  
**Docs:** http://localhost:8000/docs