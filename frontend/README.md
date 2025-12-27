# TRUSTSHIFT — Frontend Architecture (MVP)

## 0. What This Frontend Is (and Is Not)

The TRUSTSHIFT frontend is **not** an application with authority.  
It is a **pure interaction and visualization layer** over a centralized backend.

### It does NOT:
- authenticate users
- authorize actions
- calculate trust
- decide risk
- enforce rules
- store authoritative data

### It ONLY:
- collects user input
- renders backend state
- exposes role-specific views
- reflects changes in near real time

**All truth lives in the backend and database.**  
**Frontend is always replaceable.**

---

## 1. High-Level Mental Model

```
Single Backend
Single Database (MongoDB Atlas)
Single Source of Truth

    ↓ rendered through ↓

Multiple Role-Specific Frontend Views
```

Every dashboard (Worker, Customer, Supervisor, Police) is simply a **different lens** on the same backend state.

**There are no separate frontends per role — only routes.**

---

## 2. Locked Technology Stack

These choices are intentional and fixed for MVP.

| Layer | Choice |
|-------|--------|
| Framework | React |
| Build tool | Vite |
| Language | JavaScript (not TypeScript) |
| Styling | Utility-first (Tailwind CSS) |
| Icons | lucide-react (optional, minimal) |
| State management | React hooks only |
| Networking | Fetch API |
| Real-time | Polling (interval-based) |

### Explicitly NOT used:
- Redux / Zustand / MobX
- Auth libraries
- UI frameworks (MUI, AntD, Chakra)
- WebSockets
- GraphQL
- SSR / Next.js

---

## 3. Role Model (Frontend Perspective)

Frontend recognizes exactly **four roles**:

| Role | Meaning |
|------|---------|
| `worker` | Delivery / ride / field agent |
| `customer` | Citizen receiving service |
| `supervisor` | Warehouse / fleet / bank officer |
| `police` | Law enforcement |

**There is no admin role.**

Frontend does not validate roles — it trusts backend data and user selection during registration.

---

## 4. Routing Contract (ABSOLUTE)

Routes are **static** and must not be altered.

```
/
├── /register
├── /worker
│   └── /worker/profile
├── /customer
│   └── /customer/profile
├── /supervisor
│   ├── /supervisor/bind
│   └── /supervisor/shift
└── /police
```

### Important rules:
- **No protected routes**
- **No redirects based on role**
- **No guards or middleware**
- **Any route can be opened directly**

This is by design for MVP and demos.

---

## 5. Role Persistence & Identity Handling

**There is no login system.**

On registration:
1. Backend returns `uuid` and `role`
2. Frontend stores them in `localStorage`

```javascript
localStorage.setItem("uuid", "<uuid>");
localStorage.setItem("role", "<role>");
```

**Clearing localStorage = new identity.**

This simplifies:
- demos
- testing
- parallel dashboards

---

## 6. Layout System (Critical Concept)

There are exactly **two layout types**.

### 6.1 MobileLayout

**Used only for:**
- Worker
- Customer

**Characteristics:**
- Max width ≈ mobile device (≈390px)
- Centered phone-like container
- Fixed header
- Scrollable body

**Purpose:**  
Simulate real-world mobile usage without building a native app.

### 6.2 ResponsiveLayout

**Used for:**
- Register
- Supervisor
- Police

**Characteristics:**
- Desktop / tablet friendly
- Full-width content area
- Supports tables, forms, logs

**Purpose:**  
Operational dashboards, not consumer apps.

---

## 7. Page Responsibilities (Strict)

Each page has a **single responsibility**.

### `/` (Landing)
- Orientation only
- Navigation to dashboards
- No data fetching

### `/register`
- Universal self-registration
- Role selection
- Basic identity capture
- Stores UUID + role locally
- No validation logic lives here

### `/worker`
- Shows current shift status
- Shows risk state
- Displays live Shift Trust Token (STT) QR when active
- Polls backend every 3 seconds

### `/customer`
- Scans worker STT
- Displays verification result
- Logs verification via backend

### `/supervisor`
- Lists workers
- Manages workplace binding
- Starts / ends shifts
- Supervisor has operational authority, not system authority

### `/police`
- Scans worker STT
- Displays full context:
  - identity
  - workplace
  - shift status
  - risk state
  - supervisor
- Read-only access

---

## 8. Real-Time Behavior (Polling Model)

**There is no push-based real-time system.**

All dashboards use:
- `setInterval`
- backend polling every **3 seconds**

This ensures:
- predictable behavior
- easy debugging
- consistent demo results
- no hidden background state

**If backend state changes, all dashboards reflect it within 3 seconds.**

---

## 9. API Communication Rules

### Single API Client

All network calls go through:
```
src/api/client.js
```

### Rules:
- No raw `fetch` inside pages/components
- No duplicate base URLs
- No request logic inside UI components

**Frontend trusts backend responses as-is.**

---

## 10. Component Philosophy

Components are:
- **dumb**
- **reusable**
- **presentation-focused**

They **never**:
- fetch data
- own business logic
- mutate global state

### Example components:
- `ProfileCard` → displays user info
- `RiskBadge` → visual risk indicator
- `QRGenerator` → displays STT
- `QRScanner` → accepts pasted STT
- `WorkerList` → read-only table
- `EventLog` → renders logs

---

## 11. QR Handling (MVP Reality)

QR functionality is **simulated**.

- **Generator** shows STT as text
- **Scanner** accepts pasted value

### Why:
- No camera permissions
- No browser inconsistencies
- Reliable demos
- Focus on system logic

---

## 12. Styling Philosophy

Styling is:
- **minimal**
- **neutral**
- **consistent**

### Design goals:
- clarity over beauty
- inspectability over animation
- demo-readiness over polish

**This is not a consumer product UI.**

---

## 13. Error Handling

MVP-level only:
- simple alerts
- inline messages
- console logs

**No retry logic, no toasts, no global error system.**

---

## 14. What Frontend Must NEVER Do

**Do not add:**
- authentication
- authorization logic
- permission checks
- trust calculations
- risk scoring
- backend fallbacks
- caching layers
- offline sync
- analytics SDKs

**If frontend logic contradicts backend state, frontend is wrong.**

---

## 15. Running the Frontend

```bash
npm install
npm run dev
```

Frontend runs on:
```
http://localhost:5173
```

Backend must run separately on:
```
http://localhost:8000
```

---

## 16. Final Rule (Most Important)

> **TRUSTSHIFT is a trust system.**  
> **Trust systems must be simple, inspectable, and boring.**

If a change makes the frontend:
- smarter than backend
- harder to reason about
- more "magical"

**…it is the wrong change.**

---

**End of Frontend Specification**