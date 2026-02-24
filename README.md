# MyItveApp Backend

This repository contains two backend services for the **MyItveApp** project:

- **FastAPI Backend** — Python-based REST API (port `8000`)
- **Node.js Backend** — Express-based REST API (port `5000`)

Both services connect to a **MongoDB** database.

---

## Prerequisites

Ensure the following are installed before getting started:

- Python 3.8+
- Node.js v14 or higher
- MongoDB (running locally on port `27017`, or a remote cluster)

---

## 1. FastAPI Backend Setup

Navigate to the FastAPI backend directory:

```bash
cd fastAPI-backend
```

### Step 1: Create and Activate a Virtual Environment

```bash
python -m venv venv
```

**Activate:**

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the root of the `fastAPI-backend` directory:

```env
MONGO_URL=mongodb://localhost:27017/
JWT_SECRET_KEY=my-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
ADMIN_SECRET_CODE=ADMIN2024SECRET
```

### Step 4: Run the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The FastAPI server will be running at `http://localhost:8000`.  
Interactive API docs are available at `http://localhost:8000/docs`.

---

## 2. Node.js Backend Setup

Navigate to the Node.js backend directory:

```bash
cd node-backend
```

### Step 1: Install Dependencies

```bash
npm install
```

### Step 2: Configure Environment Variables

Create a `.env` file in the root of the `node-backend` directory:

```env
PORT=5000
MONGO_URI=mongodb://localhost:27017/ITVE_Database
JWT_SECRET=your_shared_secret_key_here
```

### Step 3: Run the Server

**Development mode** (with auto-reload via `nodemon`):

```bash
npm run dev
```

**Standard mode:**

```bash
npm start
```

The Node.js server will be running at `http://localhost:5000`.

---

## Project Structure

```
myitveapp-backend/
├── fastAPI-backend/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
└── node-backend/
    ├── package.json
    └── .env
```

---

## Summary

| Service   | Language | Port | Docs                          |
|-----------|----------|------|-------------------------------|
| FastAPI   | Python   | 8000 | http://localhost:8000/docs    |
| Node.js   | JS       | 5000 | —                             |
